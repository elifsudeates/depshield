"""
GitHub API Client for DepShield
================================

This module handles all interactions with the GitHub API, including:
- Fetching repository file trees
- Downloading file contents
- Extracting repository metadata

Uses the GitHub REST API v3 without authentication for public repositories.
Note: Unauthenticated requests are limited to 60 requests/hour.

Author: Elif Sude ATES
GitHub: https://github.com/elifsudeates/depshield
"""

import re
import base64
import requests
from typing import Tuple, Optional, List, Dict, Any

from .config import GITHUB_API, GITHUB_TIMEOUT, REPO_INFO_TIMEOUT, GITHUB_HEADERS
from .logger import log


def get_github_file_content(
    owner: str, 
    repo: str, 
    path: str, 
    branch: str = 'main'
) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch a single file's content from a GitHub repository.
    
    This function retrieves the raw content of a file from a GitHub repository
    using the Contents API. It automatically tries multiple branches if the
    specified branch is not found.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
        path: Path to the file within the repository
        branch: Branch name to fetch from (default: 'main')
    
    Returns:
        Tuple of (content, error):
        - On success: (file_content_string, None)
        - On failure: (None, error_message)
    
    Example:
        >>> content, error = get_github_file_content("expressjs", "express", "package.json")
        >>> if content:
        ...     print(f"Got {len(content)} bytes")
    """
    log(f"Fetching file: {path}")
    
    try:
        # Try multiple branch names in order of likelihood
        branches_to_try = [branch, 'main', 'master']
        
        for branch_name in branches_to_try:
            url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}?ref={branch_name}"
            response = requests.get(url, headers=GITHUB_HEADERS, timeout=GITHUB_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # GitHub returns file content as base64 encoded string
                if 'content' in data:
                    content = base64.b64decode(data['content']).decode('utf-8')
                    log(f"✓ Downloaded {path} ({len(content)} bytes)")
                    return content, None
        
        # File not found in any branch
        log(f"✗ File not found: {path}", "WARN")
        return None, "File not found"
        
    except requests.exceptions.Timeout:
        log(f"✗ Timeout fetching {path}", "ERROR")
        return None, "Request timed out"
        
    except requests.exceptions.RequestException as e:
        log(f"✗ Network error fetching {path}: {e}", "ERROR")
        return None, str(e)
        
    except Exception as e:
        log(f"✗ Error fetching {path}: {e}", "ERROR")
        return None, str(e)


def get_repo_tree(owner: str, repo: str) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Fetch the complete file tree of a GitHub repository.
    
    Uses the Git Trees API with recursive=1 to get all files in a single request.
    This is much more efficient than making individual requests for each file.
    
    Args:
        owner: Repository owner (username or organization)
        repo: Repository name
    
    Returns:
        Tuple of (file_list, error):
        - On success: (list_of_file_paths, None)
        - On failure: (None, error_message)
    
    Example:
        >>> files, error = get_repo_tree("expressjs", "express")
        >>> if files:
        ...     print(f"Found {len(files)} files")
    """
    log(f"Fetching repository tree for {owner}/{repo}...")
    
    try:
        # Try common default branch names
        for branch in ['main', 'master']:
            url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            log(f"Trying branch: {branch}")
            
            response = requests.get(url, headers=GITHUB_HEADERS, timeout=GITHUB_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract only file paths (not directories)
                # 'blob' type indicates a file, 'tree' indicates a directory
                files = [
                    item['path'] 
                    for item in data.get('tree', []) 
                    if item['type'] == 'blob'
                ]
                
                log(f"✓ Found {len(files)} files in repository")
                return files, None
        
        # Could not find valid branch
        log("✗ Could not fetch repository tree", "ERROR")
        return None, "Could not fetch repository tree"
        
    except requests.exceptions.Timeout:
        log("✗ Timeout fetching repository tree", "ERROR")
        return None, "Request timed out"
        
    except requests.exceptions.RequestException as e:
        log(f"✗ Network error: {e}", "ERROR")
        return None, str(e)
        
    except Exception as e:
        log(f"✗ Error: {e}", "ERROR")
        return None, str(e)


def get_repo_info(repo_url: str) -> Dict[str, Any]:
    """
    Extract repository information from a GitHub repository URL.
    
    Parses the URL to extract owner and repository name, then fetches
    additional metadata from the GitHub API.
    
    Note: Currently only GitHub repositories are supported.
    
    Args:
        repo_url: Full URL to the GitHub repository
    
    Returns:
        Dictionary containing repository information:
        {
            'name': str,        # Repository name
            'owner': str,       # Owner/organization name
            'platform': str,    # Platform (GitHub, GitLab, Bitbucket)
            'url': str,         # Original URL
            'description': str, # Repository description
            'stars': int,       # Star count (GitHub only)
            'language': str,    # Primary language
            'avatar': str       # Owner's avatar URL
        }
    
    Example:
        >>> info = get_repo_info("https://github.com/expressjs/express")
        >>> print(f"{info['owner']}/{info['name']}")
        expressjs/express
    """
    # Default values for unknown repositories
    info = {
        'name': 'Unknown',
        'owner': 'Unknown',
        'platform': 'Unknown',
        'url': repo_url,
        'description': '',
        'stars': 0,
        'language': '',
        'avatar': ''
    }
    
    # Regex pattern for GitHub URLs
    # Supports both HTTPS URLs and SSH-style URLs (git@github.com:...)
    pattern = r'github\.com[/:]([^/]+)/([^/\.]+)'
    match = re.search(pattern, repo_url)
    
    if match:
        info['owner'] = match.group(1)
        info['name'] = match.group(2).replace('.git', '')
        info['platform'] = 'GitHub'
        
        # Fetch additional metadata from GitHub API
        try:
            api_url = f"{GITHUB_API}/repos/{info['owner']}/{info['name']}"
            response = requests.get(api_url, headers=GITHUB_HEADERS, timeout=REPO_INFO_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                info['description'] = data.get('description', '') or ''
                info['stars'] = data.get('stargazers_count', 0)
                info['language'] = data.get('language', '') or ''
                info['avatar'] = data.get('owner', {}).get('avatar_url', '')
                
        except requests.exceptions.RequestException:
            # Silently fail - we already have basic info from URL
            pass
        except Exception:
            pass
    
    return info
