"""
Configuration settings for DepShield
=====================================

This module contains all configuration constants and settings used throughout
the application. Centralizing configuration makes it easier to modify settings
and maintain the codebase.

Author: Elif Sude ATES
GitHub: https://github.com/elifsudeates/depshield
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# API ENDPOINTS
# =============================================================================

# OSV (Open Source Vulnerabilities) API endpoint
# Used for checking known vulnerabilities in packages
# Documentation: https://osv.dev/docs/
OSV_API = "https://api.osv.dev/v1/query"

# GitHub API base URL
# Used for fetching repository contents without cloning
# Documentation: https://docs.github.com/en/rest
GITHUB_API = "https://api.github.com"

# GitHub Personal Access Token (optional)
# Without token: 60 requests/hour
# With token: 5000 requests/hour
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# GitHub API request headers
# Includes authentication if token is available
GITHUB_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "DepShield/1.0"
}
if GITHUB_TOKEN:
    GITHUB_HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


# =============================================================================
# SUPPORTED ECOSYSTEMS
# =============================================================================

# Mapping of package ecosystems to their respective package managers
# These are the ecosystems supported by OSV API
SUPPORTED_ECOSYSTEMS = {
    "npm": "Node.js / JavaScript",
    "PyPI": "Python",
    "RubyGems": "Ruby",
    "Go": "Go",
    "Packagist": "PHP"
}

# Dependency files to look for in repositories
DEPENDENCY_FILES = [
    "package.json",        # npm (Node.js)
    "requirements.txt",    # pip (Python)
    "Pipfile",             # pipenv (Python)
    "pyproject.toml",      # Poetry/PEP 517 (Python)
    "Gemfile.lock",        # Bundler (Ruby)
    "go.mod",              # Go modules
    "composer.json"        # Composer (PHP)
]


# =============================================================================
# DIRECTORIES TO SKIP
# =============================================================================

# Directories that should be skipped when searching for dependency files
# These typically contain dependencies, tests, or documentation
SKIP_DIRECTORIES = [
    "node_modules/",       # npm installed packages
    "vendor/",             # Composer/Go vendor directory
    "__pycache__/",        # Python bytecode cache
    ".venv/",              # Python virtual environment
    "venv/",               # Python virtual environment (alternative)
    "test/",               # Test directories
    "tests/",              # Test directories (alternative)
    "example/",            # Example code
    "examples/",           # Example code (alternative)
    "docs/",               # Documentation
    "testdata/",           # Test fixtures
    "_examples/",          # Example code (underscore prefix)
    "benchmarks/",         # Performance benchmarks
    ".github/"             # GitHub specific files
]


# =============================================================================
# REQUEST TIMEOUTS
# =============================================================================

# Timeout for GitHub API requests (in seconds)
GITHUB_TIMEOUT = 15

# Timeout for OSV API requests (in seconds)
OSV_TIMEOUT = 10

# Timeout for repository info requests (in seconds)
REPO_INFO_TIMEOUT = 5


# =============================================================================
# APPLICATION METADATA
# =============================================================================

APP_NAME = "DepShield"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Dependency Vulnerability Scanner"
APP_AUTHOR = "Elif Sude ATES"
APP_REPOSITORY = "https://github.com/elifsudeates/depshield"
