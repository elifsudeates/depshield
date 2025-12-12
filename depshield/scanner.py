"""
Vulnerability Scanner for DepShield
====================================

This module handles vulnerability scanning using the OSV (Open Source
Vulnerabilities) database API. It checks each package against known
vulnerabilities and provides real-time progress updates via SSE.

OSV API Documentation: https://osv.dev/docs/

Author: Elif Sude ATES
GitHub: https://github.com/elifsudeates/depshield
"""

import json
import requests
from typing import List, Dict, Any, Generator

from .config import OSV_API, OSV_TIMEOUT
from .logger import log
from .github_client import get_github_file_content, get_repo_tree
from .parsers import (
    find_dependency_files_in_tree,
    parse_package_json_content,
    parse_requirements_txt_content,
    parse_pipfile_content,
    parse_pyproject_toml_content,
    parse_gemfile_lock_content,
    parse_go_mod_content,
    parse_composer_json_content
)


# Mapping of internal ecosystem names to OSV API ecosystem names
ECOSYSTEM_MAP = {
    'npm': 'npm',
    'PyPI': 'PyPI',
    'RubyGems': 'RubyGems',
    'Go': 'Go',
    'Packagist': 'Packagist'
}


def check_vulnerability_osv(
    package_name: str, 
    version: str, 
    ecosystem: str
) -> List[Dict[str, Any]]:
    """
    Check a single package for known vulnerabilities using OSV API.
    
    Queries the OSV database for vulnerabilities affecting the specified
    package version. Returns detailed vulnerability information including
    CVE IDs, severity scores, and reference links.
    
    Args:
        package_name: Name of the package to check
        version: Version string of the package
        ecosystem: Package ecosystem (npm, PyPI, Go, etc.)
    
    Returns:
        List of vulnerability dictionaries, each containing:
        - id: OSV vulnerability ID
        - cve: CVE ID if available
        - summary: Brief description
        - severity: CRITICAL, HIGH, MEDIUM, LOW, or UNKNOWN
        - cvss_score: CVSS score if available
        - published: Publication date
        - references: List of reference URLs
    
    Example:
        >>> vulns = check_vulnerability_osv("lodash", "4.17.15", "npm")
        >>> if vulns:
        ...     print(f"Found {len(vulns)} vulnerabilities")
    """
    vulnerabilities = []
    
    # Map internal ecosystem name to OSV API name
    osv_ecosystem = ECOSYSTEM_MAP.get(ecosystem, ecosystem)
    
    try:
        # Construct OSV API query
        payload = {
            "package": {
                "name": package_name,
                "ecosystem": osv_ecosystem
            }
        }
        
        # Add version if specified (not 'latest')
        if version and version != 'latest':
            payload["version"] = version
        
        # Query OSV API
        response = requests.post(OSV_API, json=payload, timeout=OSV_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            # Process each vulnerability found
            if 'vulns' in data:
                for vuln in data['vulns']:
                    vulnerability = _parse_vulnerability(vuln)
                    vulnerabilities.append(vulnerability)
                    
    except requests.exceptions.Timeout:
        # Silent fail - don't block scanning for individual package timeouts
        pass
    except requests.exceptions.RequestException:
        # Silent fail for network errors
        pass
    except Exception:
        # Silent fail for unexpected errors
        pass
    
    return vulnerabilities


def _parse_vulnerability(vuln: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse raw OSV vulnerability data into standardized format.
    
    Extracts and normalizes severity information from various sources
    in the OSV response (CVSS scores, database-specific severity, etc.).
    
    Args:
        vuln: Raw vulnerability dictionary from OSV API
    
    Returns:
        Normalized vulnerability dictionary.
    """
    severity = 'UNKNOWN'
    cvss_score = None
    
    # Try to extract CVSS score from severity array
    if 'severity' in vuln:
        for sev in vuln['severity']:
            if 'score' in sev:
                cvss_score = sev.get('score')
            # Prefer CVSS v3 score
            if sev.get('type') == 'CVSS_V3':
                cvss_score = sev.get('score')
    
    # Try database-specific severity information
    if 'database_specific' in vuln:
        db_specific = vuln['database_specific']
        if 'severity' in db_specific:
            severity = db_specific['severity']
        if 'cvss' in db_specific:
            cvss_score = db_specific['cvss'].get('score')
    
    # Calculate severity from CVSS score if available
    if cvss_score:
        try:
            score = float(cvss_score) if isinstance(cvss_score, str) else cvss_score
            if score >= 9.0:
                severity = 'CRITICAL'
            elif score >= 7.0:
                severity = 'HIGH'
            elif score >= 4.0:
                severity = 'MEDIUM'
            else:
                severity = 'LOW'
        except (ValueError, TypeError):
            pass
    
    # Extract CVE ID from aliases
    cve_id = None
    if 'aliases' in vuln:
        for alias in vuln['aliases']:
            if alias.startswith('CVE-'):
                cve_id = alias
                break
    
    return {
        'id': vuln.get('id', 'Unknown'),
        'cve': cve_id,
        'summary': vuln.get('summary', vuln.get('details', 'No description available'))[:200],
        'severity': severity,
        'cvss_score': cvss_score,
        'published': vuln.get('published', 'Unknown'),
        'references': [ref.get('url') for ref in vuln.get('references', [])[:3]]
    }


def _send_event(event_type: str, data: Dict[str, Any]) -> str:
    """
    Format a Server-Sent Event (SSE) message.
    
    Args:
        event_type: Type of event (status, complete, error)
        data: Event data dictionary
    
    Returns:
        Formatted SSE message string.
    """
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


def scan_with_progress(owner: str, repo: str) -> Generator[str, None, None]:
    """
    Scan a repository for dependency vulnerabilities with real-time progress.
    
    This generator function performs a complete vulnerability scan and yields
    SSE-formatted progress updates. It's designed to be used with Flask's
    streaming response for real-time frontend updates.
    
    Scanning process:
    1. Fetch repository file tree from GitHub
    2. Identify dependency files
    3. Download and parse each dependency file
    4. Deduplicate dependencies
    5. Check each unique package against OSV database
    6. Compile and return results
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
    
    Yields:
        SSE-formatted event strings with progress updates.
        Event types:
        - 'status': Progress update with message and percentage
        - 'complete': Final results
        - 'error': Error message
    
    Example:
        >>> for event in scan_with_progress("expressjs", "express"):
        ...     print(event)  # SSE formatted string
    """
    yield _send_event('status', {'message': 'Connecting to GitHub API...', 'progress': 5})
    log(f"Starting scan for {owner}/{repo}")
    
    # =========================================================================
    # STEP 1: Fetch repository file tree
    # =========================================================================
    yield _send_event('status', {'message': 'Fetching repository structure...', 'progress': 10})
    file_list, error = get_repo_tree(owner, repo)
    
    if error:
        yield _send_event('error', {'message': f'Could not fetch repository: {error}'})
        return
    
    yield _send_event('status', {
        'message': f'Found {len(file_list)} files in repository', 
        'progress': 15
    })
    
    # =========================================================================
    # STEP 2: Find dependency files
    # =========================================================================
    yield _send_event('status', {'message': 'Searching for dependency files...', 'progress': 20})
    dep_files = find_dependency_files_in_tree(file_list)
    
    # Handle case where no dependency files are found
    if not dep_files:
        yield _send_event('status', {'message': 'No dependency files found', 'progress': 100})
        yield _send_event('complete', {
            'results': _create_empty_results()
        })
        return
    
    yield _send_event('status', {
        'message': f'Found {len(dep_files)} dependency files', 
        'progress': 25, 
        'files': dep_files
    })
    
    # Initialize results structure
    results = _create_empty_results()
    all_dependencies = []
    
    # =========================================================================
    # STEP 3: Parse each dependency file
    # =========================================================================
    file_progress_step = 20 / max(len(dep_files), 1)
    
    for i, file_path in enumerate(dep_files):
        progress = 25 + int(i * file_progress_step)
        yield _send_event('status', {
            'message': f'Downloading: {file_path}', 
            'progress': progress, 
            'current_file': file_path
        })
        
        # Download file content
        content, error = get_github_file_content(owner, repo, file_path)
        if error or not content:
            log(f"Skipping {file_path}: {error}")
            continue
        
        results['files_scanned'].append(file_path)
        
        yield _send_event('status', {
            'message': f'Parsing: {file_path}', 
            'progress': progress + 2, 
            'current_file': file_path
        })
        
        # Parse dependencies based on file type
        filename = file_path.split('/')[-1]
        deps = _parse_dependency_file(filename, content)
        
        all_dependencies.extend(deps)
        yield _send_event('status', {
            'message': f'Found {len(deps)} dependencies in {filename}', 
            'progress': progress + 5, 
            'deps_count': len(deps)
        })
    
    # =========================================================================
    # STEP 4: Deduplicate dependencies
    # =========================================================================
    yield _send_event('status', {'message': 'Removing duplicate dependencies...', 'progress': 50})
    
    seen = set()
    unique_deps = []
    for dep in all_dependencies:
        key = f"{dep['ecosystem']}:{dep['name']}:{dep['version']}"
        if key not in seen:
            seen.add(key)
            unique_deps.append(dep)
    
    results['dependencies'] = unique_deps
    results['summary']['total_dependencies'] = len(unique_deps)
    
    # Count dependencies by ecosystem
    for dep in unique_deps:
        eco = dep['ecosystem']
        results['ecosystems'][eco] = results['ecosystems'].get(eco, 0) + 1
    
    yield _send_event('status', {
        'message': f'Total unique dependencies: {len(unique_deps)}', 
        'progress': 52
    })
    log(f"Total unique dependencies: {len(unique_deps)}")
    
    # Handle case where no dependencies were found
    if len(unique_deps) == 0:
        yield _send_event('status', {'message': 'No dependencies to scan', 'progress': 100})
        yield _send_event('complete', {'results': results})
        return
    
    # =========================================================================
    # STEP 5: Check vulnerabilities for each package
    # =========================================================================
    vulnerable_packages = set()
    vuln_progress_step = 45 / len(unique_deps)
    
    yield _send_event('status', {
        'message': f'Checking {len(unique_deps)} packages for vulnerabilities...', 
        'progress': 55
    })
    
    for i, dep in enumerate(unique_deps):
        progress = 55 + int(i * vuln_progress_step)
        
        # Send progress update every 5 packages to reduce overhead
        if i % 5 == 0 or i == len(unique_deps) - 1:
            yield _send_event('status', {
                'message': f'Checking: {dep["name"]}@{dep["version"]} ({i+1}/{len(unique_deps)})',
                'progress': progress,
                'current_package': dep['name'],
                'packages_checked': i + 1,
                'total_packages': len(unique_deps)
            })
        
        log(f"Checking vulnerability: {dep['ecosystem']}/{dep['name']}@{dep['version']} ({i+1}/{len(unique_deps)})")
        
        # Query OSV for vulnerabilities
        vulns = check_vulnerability_osv(dep['name'], dep['version'], dep['ecosystem'])
        
        if vulns:
            log(f"  ⚠ Found {len(vulns)} vulnerabilities!")
            vulnerable_packages.add(f"{dep['ecosystem']}:{dep['name']}")
            
            # Add vulnerability details to results
            for vuln in vulns:
                vuln['package'] = dep['name']
                vuln['version'] = dep['version']
                vuln['ecosystem'] = dep['ecosystem']
                results['vulnerabilities'].append(vuln)
                
                # Update severity counts
                severity = vuln['severity'].upper()
                if severity == 'CRITICAL':
                    results['summary']['critical'] += 1
                elif severity == 'HIGH':
                    results['summary']['high'] += 1
                elif severity == 'MEDIUM':
                    results['summary']['medium'] += 1
                elif severity == 'LOW':
                    results['summary']['low'] += 1
                else:
                    results['summary']['unknown'] += 1
    
    # Finalize summary counts
    results['summary']['vulnerable_dependencies'] = len(vulnerable_packages)
    results['summary']['total_vulnerabilities'] = len(results['vulnerabilities'])
    
    log(f"Scan complete! Found {len(results['vulnerabilities'])} vulnerabilities in {len(vulnerable_packages)} packages")
    
    # =========================================================================
    # STEP 6: Return final results
    # =========================================================================
    yield _send_event('status', {'message': 'Scan complete!', 'progress': 100})
    yield _send_event('complete', {'results': results})


def _create_empty_results() -> Dict[str, Any]:
    """Create an empty results structure."""
    return {
        'dependencies': [],
        'vulnerabilities': [],
        'summary': {
            'total_dependencies': 0,
            'vulnerable_dependencies': 0,
            'total_vulnerabilities': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'unknown': 0
        },
        'ecosystems': {},
        'files_scanned': []
    }


def _parse_dependency_file(filename: str, content: str) -> List[Dict[str, str]]:
    """
    Parse a dependency file and return list of dependencies.
    
    Routes to the appropriate parser based on filename.
    
    Args:
        filename: Name of the dependency file
        content: Raw content of the file
    
    Returns:
        List of dependency dictionaries.
    """
    parsers = {
        'package.json': parse_package_json_content,
        'requirements.txt': parse_requirements_txt_content,
        'Pipfile': parse_pipfile_content,
        'pyproject.toml': parse_pyproject_toml_content,
        'Gemfile.lock': parse_gemfile_lock_content,
        'go.mod': parse_go_mod_content,
        'composer.json': parse_composer_json_content,
    }
    
    parser = parsers.get(filename)
    if parser:
        return parser(content)
    return []
