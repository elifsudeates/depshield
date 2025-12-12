"""
DepShield - Dependency Vulnerability Scanner
============================================

A SSDLC (Secure Software Development Life Cycle) tool for scanning Git repositories
for dependency vulnerabilities using the OSV (Open Source Vulnerabilities) database.

Author: Elif Sude ATES
GitHub: https://github.com/elifsudeates/depshield
License: MIT
"""

from .config import OSV_API, GITHUB_API
from .logger import log
from .github_client import get_github_file_content, get_repo_tree, get_repo_info
from .parsers import (
    parse_package_json_content,
    parse_requirements_txt_content,
    parse_pipfile_content,
    parse_pyproject_toml_content,
    parse_gemfile_lock_content,
    parse_go_mod_content,
    parse_composer_json_content,
    find_dependency_files_in_tree
)
from .scanner import check_vulnerability_osv, scan_with_progress

__version__ = "1.0.0"
__author__ = "Elif Sude ATES"
__email__ = "github.com/elifsudeates"

__all__ = [
    "OSV_API",
    "GITHUB_API",
    "log",
    "get_github_file_content",
    "get_repo_tree",
    "get_repo_info",
    "parse_package_json_content",
    "parse_requirements_txt_content",
    "parse_pipfile_content",
    "parse_pyproject_toml_content",
    "parse_gemfile_lock_content",
    "parse_go_mod_content",
    "parse_composer_json_content",
    "find_dependency_files_in_tree",
    "check_vulnerability_osv",
    "scan_with_progress",
]
