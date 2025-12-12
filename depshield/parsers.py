"""
Dependency File Parsers for DepShield
======================================

This module contains parsers for various package manager dependency files.
Each parser extracts dependency information (name, version, ecosystem) from
the respective file format.

Supported formats:
- package.json (npm/Node.js)
- requirements.txt (pip/Python)
- Pipfile (pipenv/Python)
- pyproject.toml (Poetry/Python)
- Gemfile.lock (Bundler/Ruby)
- go.mod (Go modules)
- composer.json (Composer/PHP)

Author: Elif Sude ATES
GitHub: https://github.com/elifsudeates/depshield
"""

import json
import re
from typing import List, Dict, Any, Tuple

from .config import DEPENDENCY_FILES, SKIP_DIRECTORIES
from .logger import log


def parse_package_json_content(content: str) -> List[Dict[str, str]]:
    """
    Parse package.json content and extract npm dependencies.
    
    Extracts dependencies from all dependency sections:
    - dependencies
    - devDependencies
    - peerDependencies
    - optionalDependencies
    
    Args:
        content: Raw JSON content of package.json
    
    Returns:
        List of dependency dictionaries with keys:
        - name: Package name
        - version: Version string (cleaned of range operators)
        - type: Dependency type (dependencies, devDependencies, etc.)
        - ecosystem: Always "npm"
    
    Example:
        >>> deps = parse_package_json_content('{"dependencies": {"express": "^4.17.1"}}')
        >>> deps[0]
        {'name': 'express', 'version': '4.17.1', 'type': 'dependencies', 'ecosystem': 'npm'}
    """
    dependencies = []
    
    try:
        data = json.loads(content)
        
        # All possible dependency sections in package.json
        dep_types = ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies']
        
        for dep_type in dep_types:
            if dep_type in data:
                for name, version in data[dep_type].items():
                    # Clean version string - remove range operators (^, ~, >=, etc.)
                    clean_version = re.sub(r'^[\^~>=<]', '', str(version))
                    clean_version = clean_version.split(' ')[0]  # Take first part if range
                    
                    dependencies.append({
                        'name': name,
                        'version': clean_version,
                        'type': dep_type,
                        'ecosystem': 'npm'
                    })
        
        log(f"  Parsed {len(dependencies)} npm dependencies")
        
    except json.JSONDecodeError as e:
        log(f"  Error parsing package.json: Invalid JSON - {e}", "ERROR")
    except Exception as e:
        log(f"  Error parsing package.json: {e}", "ERROR")
    
    return dependencies


def parse_requirements_txt_content(content: str) -> List[Dict[str, str]]:
    """
    Parse requirements.txt content and extract Python dependencies.
    
    Handles various pip requirement formats:
    - Simple: package==1.0.0
    - Range: package>=1.0.0,<2.0.0
    - No version: package
    - Comments: # ignored
    - Flags: -r, -e (ignored)
    
    Args:
        content: Raw content of requirements.txt
    
    Returns:
        List of dependency dictionaries for PyPI ecosystem.
    
    Example:
        >>> deps = parse_requirements_txt_content("flask==2.0.0\\nrequests>=2.25.0")
        >>> len(deps)
        2
    """
    dependencies = []
    
    try:
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip empty lines, comments, and pip flags
            if not line or line.startswith('#') or line.startswith('-'):
                continue
            
            # Parse package name and optional version
            # Matches: package, package==1.0, package>=1.0, etc.
            match = re.match(r'^([a-zA-Z0-9_-]+)([=<>!]+)?(.+)?$', line)
            
            if match:
                name = match.group(1)
                version = match.group(3) if match.group(3) else 'latest'
                version = version.split(',')[0].strip()  # Take first constraint
                
                dependencies.append({
                    'name': name,
                    'version': version,
                    'type': 'dependencies',
                    'ecosystem': 'PyPI'
                })
        
        log(f"  Parsed {len(dependencies)} PyPI dependencies")
        
    except Exception as e:
        log(f"  Error parsing requirements.txt: {e}", "ERROR")
    
    return dependencies


def parse_pipfile_content(content: str) -> List[Dict[str, str]]:
    """
    Parse Pipfile content and extract Python dependencies.
    
    Pipfile uses TOML format with [packages] and [dev-packages] sections.
    
    Args:
        content: Raw TOML content of Pipfile
    
    Returns:
        List of dependency dictionaries for PyPI ecosystem.
    """
    dependencies = []
    
    try:
        import toml
        data = toml.loads(content)
        
        # Parse both regular and dev packages
        for dep_type in ['packages', 'dev-packages']:
            if dep_type in data:
                for name, version in data[dep_type].items():
                    # Version can be a string or a dict with version key
                    if isinstance(version, dict):
                        version = version.get('version', '*')
                    
                    # Clean version string
                    version = str(version).replace('*', 'latest').replace('==', '').replace('>=', '')
                    
                    dependencies.append({
                        'name': name,
                        'version': version,
                        'type': dep_type,
                        'ecosystem': 'PyPI'
                    })
        
        log(f"  Parsed {len(dependencies)} PyPI dependencies from Pipfile")
        
    except ImportError:
        log("  Error: toml package not installed", "ERROR")
    except Exception as e:
        log(f"  Error parsing Pipfile: {e}", "ERROR")
    
    return dependencies


def parse_pyproject_toml_content(content: str) -> List[Dict[str, str]]:
    """
    Parse pyproject.toml content and extract Python dependencies.
    
    Supports multiple formats:
    - PEP 517/518 build-system requirements ([build-system].requires)
    - PEP 621 format ([project.dependencies])
    - Poetry format ([tool.poetry.dependencies])
    
    Args:
        content: Raw TOML content of pyproject.toml
    
    Returns:
        List of dependency dictionaries for PyPI ecosystem.
    """
    dependencies = []
    
    try:
        import toml
        data = toml.loads(content)
        
        # ---------------------------------------------------------------------
        # Parse PEP 517/518 build-system requirements
        # Example: [build-system]
        #          requires = ["meson-python>=0.18.0", "Cython>=3.0.6"]
        # ---------------------------------------------------------------------
        if 'build-system' in data and 'requires' in data['build-system']:
            for dep in data['build-system']['requires']:
                # Parse dependency string: "package>=version" or "package[extra]>=version"
                match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[[^\]]+\])?([=<>!~]+)?(.+)?$', dep)
                if match:
                    name = match.group(1)
                    version = match.group(3) if match.group(3) else 'latest'
                    # Clean version - remove trailing constraints after comma
                    version = version.split(',')[0].strip()
                    
                    dependencies.append({
                        'name': name,
                        'version': version,
                        'type': 'build-requires',
                        'ecosystem': 'PyPI'
                    })
        
        # ---------------------------------------------------------------------
        # Parse Poetry format
        # Example: [tool.poetry.dependencies]
        #          flask = "^2.0.0"
        # ---------------------------------------------------------------------
        if 'tool' in data and 'poetry' in data['tool']:
            poetry = data['tool']['poetry']
            
            for dep_type in ['dependencies', 'dev-dependencies']:
                if dep_type in poetry:
                    for name, version in poetry[dep_type].items():
                        # Skip Python version specification
                        if name.lower() == 'python':
                            continue
                        
                        # Version can be string or dict
                        if isinstance(version, dict):
                            version = version.get('version', '*')
                        
                        # Clean version string
                        version = str(version).replace('^', '').replace('~', '').replace('*', 'latest')
                        
                        dependencies.append({
                            'name': name,
                            'version': version,
                            'type': dep_type,
                            'ecosystem': 'PyPI'
                        })
        
        # ---------------------------------------------------------------------
        # Parse PEP 621 format
        # Example: [project]
        #          dependencies = ["flask>=2.0.0", "requests"]
        # ---------------------------------------------------------------------
        if 'project' in data:
            project = data['project']
            
            # Main dependencies
            if 'dependencies' in project:
                for dep in project['dependencies']:
                    match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[[^\]]+\])?([=<>!~]+)?(.+)?$', dep)
                    if match:
                        name = match.group(1)
                        version = match.group(3) if match.group(3) else 'latest'
                        
                        dependencies.append({
                            'name': name,
                            'version': version.split(',')[0].strip(),
                            'type': 'dependencies',
                            'ecosystem': 'PyPI'
                        })
            
            # Optional dependencies (extras)
            if 'optional-dependencies' in project:
                for group_name, deps in project['optional-dependencies'].items():
                    for dep in deps:
                        match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[[^\]]+\])?([=<>!~]+)?(.+)?$', dep)
                        if match:
                            name = match.group(1)
                            version = match.group(3) if match.group(3) else 'latest'
                            
                            dependencies.append({
                                'name': name,
                                'version': version.split(',')[0].strip(),
                                'type': f'optional-{group_name}',
                                'ecosystem': 'PyPI'
                            })
        
        log(f"  Parsed {len(dependencies)} PyPI dependencies from pyproject.toml")
        
    except ImportError:
        log("  Error: toml package not installed", "ERROR")
    except Exception as e:
        log(f"  Error parsing pyproject.toml: {e}", "ERROR")
    
    return dependencies


def parse_gemfile_lock_content(content: str) -> List[Dict[str, str]]:
    """
    Parse Gemfile.lock content and extract Ruby dependencies.
    
    Gemfile.lock contains resolved dependencies with exact versions
    under the 'specs:' section with 4-space indentation.
    
    Args:
        content: Raw content of Gemfile.lock
    
    Returns:
        List of dependency dictionaries for RubyGems ecosystem.
    """
    dependencies = []
    
    try:
        in_specs = False
        
        for line in content.split('\n'):
            # Look for specs: section
            if 'specs:' in line:
                in_specs = True
                continue
            
            if in_specs:
                # End of specs section (line doesn't start with space)
                if line and not line.startswith(' '):
                    in_specs = False
                    continue
                
                # Parse gem entries (4 spaces indent, name (version) format)
                match = re.match(r'^\s{4}([a-zA-Z0-9_-]+)\s+\(([^)]+)\)', line)
                if match:
                    dependencies.append({
                        'name': match.group(1),
                        'version': match.group(2),
                        'type': 'dependencies',
                        'ecosystem': 'RubyGems'
                    })
        
        log(f"  Parsed {len(dependencies)} RubyGems dependencies")
        
    except Exception as e:
        log(f"  Error parsing Gemfile.lock: {e}", "ERROR")
    
    return dependencies


def parse_go_mod_content(content: str) -> List[Dict[str, str]]:
    """
    Parse go.mod content and extract Go module dependencies.
    
    Handles both block format:
        require (
            module/path v1.0.0
        )
    
    And single-line format:
        require module/path v1.0.0
    
    Args:
        content: Raw content of go.mod
    
    Returns:
        List of dependency dictionaries for Go ecosystem.
    """
    dependencies = []
    
    try:
        # Parse block-style require statements
        require_block = re.search(r'require\s*\((.*?)\)', content, re.DOTALL)
        
        if require_block:
            for line in require_block.group(1).split('\n'):
                # Match: module/path v1.0.0
                match = re.match(r'\s*([^\s]+)\s+v?([^\s]+)', line)
                if match and not match.group(1).startswith('//'):
                    dependencies.append({
                        'name': match.group(1),
                        'version': match.group(2),
                        'type': 'dependencies',
                        'ecosystem': 'Go'
                    })
        
        # Parse single-line require statements
        for match in re.finditer(r'^require\s+([^\s]+)\s+v?([^\s\n]+)', content, re.MULTILINE):
            dependencies.append({
                'name': match.group(1),
                'version': match.group(2),
                'type': 'dependencies',
                'ecosystem': 'Go'
            })
        
        log(f"  Parsed {len(dependencies)} Go dependencies")
        
    except Exception as e:
        log(f"  Error parsing go.mod: {e}", "ERROR")
    
    return dependencies


def parse_composer_json_content(content: str) -> List[Dict[str, str]]:
    """
    Parse composer.json content and extract PHP dependencies.
    
    Extracts from 'require' and 'require-dev' sections,
    filtering out PHP version and extension requirements.
    
    Args:
        content: Raw JSON content of composer.json
    
    Returns:
        List of dependency dictionaries for Packagist ecosystem.
    """
    dependencies = []
    
    try:
        data = json.loads(content)
        
        for dep_type in ['require', 'require-dev']:
            if dep_type in data:
                for name, version in data[dep_type].items():
                    # Skip PHP version and extension requirements
                    if name.startswith('php') or name.startswith('ext-'):
                        continue
                    
                    # Clean version string
                    version = re.sub(r'^[\^~>=<]', '', str(version)).split(' ')[0]
                    
                    dependencies.append({
                        'name': name,
                        'version': version,
                        'type': dep_type,
                        'ecosystem': 'Packagist'
                    })
        
        log(f"  Parsed {len(dependencies)} Packagist dependencies")
        
    except json.JSONDecodeError as e:
        log(f"  Error parsing composer.json: Invalid JSON - {e}", "ERROR")
    except Exception as e:
        log(f"  Error parsing composer.json: {e}", "ERROR")
    
    return dependencies


def find_dependency_files_in_tree(file_list: List[str]) -> List[str]:
    """
    Find all dependency files in a repository file tree.
    
    Filters the file list to find supported dependency files,
    excluding files in test/example/vendor directories.
    Results are sorted by depth (root files first).
    
    Args:
        file_list: List of all file paths in the repository
    
    Returns:
        Sorted list of dependency file paths found.
    
    Example:
        >>> files = ["package.json", "test/package.json", "src/utils.js"]
        >>> find_dependency_files_in_tree(files)
        ['package.json']  # test/package.json is excluded
    """
    found_files = []
    
    for file_path in file_list:
        # Check if file is in a directory we should skip
        should_skip = False
        for skip_dir in SKIP_DIRECTORIES:
            if skip_dir in file_path:
                should_skip = True
                break
        
        if should_skip:
            continue
        
        # Check if filename matches a known dependency file
        filename = file_path.split('/')[-1]
        if filename in DEPENDENCY_FILES:
            depth = file_path.count('/')
            found_files.append((file_path, depth))
    
    # Sort by depth (shallow files first - more likely to be main config)
    found_files.sort(key=lambda x: x[1])
    
    result = [f[0] for f in found_files]
    log(f"Found {len(result)} dependency files to analyze")
    
    return result


# Parser registry for easy file-to-parser mapping
PARSERS = {
    'package.json': parse_package_json_content,
    'requirements.txt': parse_requirements_txt_content,
    'Pipfile': parse_pipfile_content,
    'pyproject.toml': parse_pyproject_toml_content,
    'Gemfile.lock': parse_gemfile_lock_content,
    'go.mod': parse_go_mod_content,
    'composer.json': parse_composer_json_content,
}


def get_parser_for_file(filename: str):
    """
    Get the appropriate parser function for a dependency file.
    
    Args:
        filename: Name of the dependency file
    
    Returns:
        Parser function or None if no parser exists.
    """
    return PARSERS.get(filename)
