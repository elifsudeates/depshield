<div align="center">
  <img src="static/logo.svg" alt="DepShield Logo" width="128" height="128">
  
  # DepShield
  
  **Dependency Vulnerability Scanner for Secure Software Development**
  
  [![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![OSV Database](https://img.shields.io/badge/Powered%20by-OSV%20Database-orange.svg)](https://osv.dev/)
  
  [Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [API](#-api) • [Docker](#-docker) • [Contributing](#-contributing)
</div>

---

## 🛡️ About

DepShield is an **SSDLC (Secure Software Development Life Cycle)** tool that scans Git repositories for known vulnerabilities in their dependencies. It leverages the [OSV (Open Source Vulnerabilities)](https://osv.dev/) database to provide accurate, up-to-date vulnerability information.

### Why DepShield?

- **Fast**: Uses GitHub API to fetch files directly — no cloning required
- **Real-time Progress**: Server-Sent Events (SSE) provide live scanning updates
- **Multi-ecosystem**: Supports npm, PyPI, RubyGems, Go, and Packagist
- **Beautiful UI**: Modern, responsive web interface with Bold Berry theme
- **Export Ready**: Download reports in JSON or CSV format
- **No Account Required**: Works with public repositories out of the box

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Multi-Ecosystem Scanning** | npm, PyPI, RubyGems, Go, Packagist |
| ⚡ **Lightning Fast** | GitHub API-based scanning, no git clone needed |
| 📊 **Real-time Progress** | Live updates via Server-Sent Events |
| 🎨 **Modern UI** | Beautiful Bold Berry color theme |
| 📥 **Export Reports** | JSON and CSV export with timestamps |
| 🏷️ **CVE Detection** | Full CVE IDs and CVSS scores |
| 🔗 **Reference Links** | Direct links to vulnerability details |
| 🐳 **Docker Ready** | Easy deployment with Docker |

### Supported Dependency Files

| Ecosystem | Files |
|-----------|-------|
| **npm** | `package.json` |
| **Python** | `requirements.txt`, `Pipfile`, `pyproject.toml` |
| **Ruby** | `Gemfile.lock` |
| **Go** | `go.mod` |
| **PHP** | `composer.json` |

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/elifsudeates/depshield.git
cd depshield

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Open your browser and navigate to `http://127.0.0.1:5000`

---

## 📖 Usage

### Web Interface

1. Enter a GitHub repository URL (e.g., `https://github.com/expressjs/express`)
2. Click **"Scan Repository"**
3. Watch real-time progress as dependencies are analyzed
4. View vulnerability results sorted by severity
5. Export reports in JSON or CSV format

### Screenshots

<details>
<summary>Click to view screenshots</summary>

#### Scanning in Progress
The scanner shows real-time progress with the current package being checked.

#### Results Dashboard
View all vulnerabilities organized by severity with CVE details.

</details>

---

## 🔌 API

DepShield provides a REST API for programmatic access.

### Get Repository Info

```http
POST /api/repo-info
Content-Type: application/json

{
  "url": "https://github.com/expressjs/express"
}
```

**Response:**
```json
{
  "name": "express",
  "owner": "expressjs",
  "platform": "GitHub",
  "description": "Fast, unopinionated, minimalist web framework for node.",
  "stars": 65000,
  "language": "JavaScript",
  "avatar": "https://avatars.githubusercontent.com/u/5658226"
}
```

### Scan Repository (Streaming)

```http
GET /api/scan-stream?url=https://github.com/expressjs/express
```

Returns Server-Sent Events with real-time progress updates.

### Scan Repository (Non-Streaming)

```http
POST /api/scan
Content-Type: application/json

{
  "url": "https://github.com/expressjs/express"
}
```

### Export Results

```http
POST /api/export/json
POST /api/export/csv
Content-Type: application/json

{ /* scan results */ }
```

---

## 🐳 Docker

### Build and Run

```bash
# Build the image
docker build -t depshield .

# Run the container
docker run -p 5000:5000 depshield
```

### Docker Compose

```yaml
version: '3.8'
services:
  depshield:
    build: .
    ports:
      - "5000:5000"
    restart: unless-stopped
```

---

## 📁 Project Structure

```
depshield/
├── app.py                 # Flask application entry point
├── depshield/             # Core scanning modules
│   ├── __init__.py        # Package initialization
│   ├── config.py          # Configuration settings
│   ├── logger.py          # Logging utilities
│   ├── github_client.py   # GitHub API client
│   ├── parsers.py         # Dependency file parsers
│   └── scanner.py         # Vulnerability scanner
├── static/                # Frontend assets
│   ├── index.html         # Main web interface
│   ├── logo.svg           # Application logo
│   └── favicon.svg        # Browser favicon
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
├── TEST_REPOS.md          # Test repository links
└── README.md              # This file
```

---

## 🧪 Test Repositories

Check out [TEST_REPOS.md](TEST_REPOS.md) for a curated list of repositories organized by programming language for testing DepShield.

**Quick test links:**
- Small: `https://github.com/expressjs/express`
- Medium: `https://github.com/pallets/flask`
- Large: `https://github.com/django/django`

---

## 🔧 Configuration

Configuration options are available in `depshield/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `OSV_API` | `https://api.osv.dev/v1/query` | OSV API endpoint |
| `GITHUB_API` | `https://api.github.com` | GitHub API endpoint |
| `GITHUB_TIMEOUT` | `15` | GitHub request timeout (seconds) |
| `OSV_TIMEOUT` | `10` | OSV request timeout (seconds) |

---

## ⚠️ Limitations

- **GitHub Only**: Currently only supports GitHub repositories
- **Public Repos**: Works with public repositories (private repos require authentication)
- **Rate Limits**: GitHub API has rate limits (60 requests/hour unauthenticated)
- **Nested Dependencies**: Only scans direct dependencies, not transitive ones

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [OSV (Open Source Vulnerabilities)](https://osv.dev/) for the vulnerability database
- [Bulma](https://bulma.io/) for the CSS framework
- [Tabler Icons](https://tabler-icons.io/) for the icon set
- [Flask](https://flask.palletsprojects.com/) for the web framework

---

<div align="center">
  <p>Made with ❤️ by <a href="https://github.com/elifsudeates">Elif Sude ATES</a></p>
  <p>
    <a href="https://github.com/elifsudeates/depshield/issues">Report Bug</a>
    •
    <a href="https://github.com/elifsudeates/depshield/issues">Request Feature</a>
  </p>
</div>
