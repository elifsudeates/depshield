"""
DepShield - Dependency Vulnerability Scanner
============================================

A SSDLC (Secure Software Development Life Cycle) tool for scanning Git
repositories for dependency vulnerabilities using the OSV database.

This is the main Flask application that provides:
- Web interface for scanning repositories
- REST API for repository info and scanning
- Server-Sent Events (SSE) for real-time progress updates
- Export functionality for JSON and CSV reports

Author: Elif Sude ATES
GitHub: https://github.com/elifsudeates/depshield
License: MIT
"""

from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
import json
import csv
import io
from datetime import datetime

# Import DepShield modules
from depshield import (
    log,
    get_repo_info,
    scan_with_progress
)
from depshield.config import APP_NAME, APP_VERSION


# =============================================================================
# FLASK APPLICATION SETUP
# =============================================================================

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable Cross-Origin Resource Sharing for API access


# =============================================================================
# STATIC FILE ROUTES
# =============================================================================

@app.route('/')
def index():
    """
    Serve the main web interface.
    
    Returns the index.html file from the static folder.
    """
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """
    Serve static files (CSS, JS, images, etc.).
    
    Args:
        filename: Path to the static file
    
    Returns:
        The requested static file.
    """
    return send_from_directory('static', filename)


# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/api/repo-info', methods=['POST'])
def api_repo_info():
    """
    Get basic repository information without cloning.
    
    Request Body:
        {
            "url": "https://github.com/owner/repo"
        }
    
    Returns:
        JSON object with repository metadata:
        {
            "name": "repo",
            "owner": "owner",
            "platform": "GitHub",
            "description": "...",
            "stars": 1234,
            "language": "JavaScript",
            "avatar": "https://..."
        }
    """
    data = request.json
    repo_url = data.get('url', '').strip()
    
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400
    
    info = get_repo_info(repo_url)
    return jsonify(info)


@app.route('/api/scan-stream', methods=['GET'])
def api_scan_stream():
    """
    Scan a repository with real-time progress updates via SSE.
    
    Uses Server-Sent Events to stream progress updates to the client
    in real-time. This allows the frontend to show accurate progress
    as each dependency is checked.
    
    Query Parameters:
        url: Repository URL to scan
    
    Returns:
        SSE stream with events:
        - 'start': Scanning started with repo info
        - 'status': Progress update (message, percentage)
        - 'complete': Final results
        - 'error': Error occurred
    """
    repo_url = request.args.get('url', '').strip()
    
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400
    
    # Get repository information
    repo_info = get_repo_info(repo_url)
    
    # Currently only GitHub is supported
    if repo_info['platform'] != 'GitHub':
        return jsonify({'error': 'Currently only GitHub repositories are supported'}), 400
    
    if repo_info['owner'] == 'Unknown' or repo_info['name'] == 'Unknown':
        return jsonify({'error': 'Invalid repository URL'}), 400
    
    def generate():
        """Generator function for SSE stream."""
        # Send initial event with repo info
        yield f"data: {json.dumps({'type': 'start', 'repo_info': repo_info})}\n\n"
        
        # Stream scan progress
        for event in scan_with_progress(repo_info['owner'], repo_info['name']):
            yield event
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )


@app.route('/api/scan', methods=['POST'])
def api_scan():
    """
    Legacy scan endpoint (non-streaming).
    
    Performs a complete scan and returns results when finished.
    Use /api/scan-stream for real-time progress updates.
    
    Request Body:
        {
            "url": "https://github.com/owner/repo"
        }
    
    Returns:
        JSON object with scan results.
    """
    data = request.json
    repo_url = data.get('url', '').strip()
    
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400
    
    repo_info = get_repo_info(repo_url)
    
    if repo_info['platform'] != 'GitHub':
        return jsonify({'error': 'Currently only GitHub repositories are supported'}), 400
    
    if repo_info['owner'] == 'Unknown' or repo_info['name'] == 'Unknown':
        return jsonify({'error': 'Invalid repository URL'}), 400
    
    try:
        results = None
        
        # Process all events from the scanner
        for event in scan_with_progress(repo_info['owner'], repo_info['name']):
            event_data = json.loads(event.replace('data: ', '').strip())
            
            if event_data.get('type') == 'complete':
                results = event_data['results']
            elif event_data.get('type') == 'error':
                return jsonify({'error': event_data['message']}), 400
        
        if results:
            results['repo_info'] = repo_info
            results['scan_time'] = datetime.now().isoformat()
            return jsonify(results)
        else:
            return jsonify({'error': 'Scan failed'}), 500
    
    except Exception as e:
        log(f"Scan error: {e}", "ERROR")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# EXPORT ROUTES
# =============================================================================

@app.route('/api/export/json', methods=['POST'])
def api_export_json():
    """
    Export scan results as JSON file.
    
    Request Body:
        Full scan results object
    
    Returns:
        JSON file download.
    """
    data = request.json
    
    response = Response(
        json.dumps(data, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment;filename=vulnerability-report.json'}
    )
    return response


@app.route('/api/export/csv', methods=['POST'])
def api_export_csv():
    """
    Export scan results as CSV file.
    
    Request Body:
        Full scan results object
    
    Returns:
        CSV file download with vulnerability data.
    """
    data = request.json
    vulnerabilities = data.get('vulnerabilities', [])
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write CSV header
    writer.writerow([
        'Package', 'Version', 'Ecosystem', 
        'Vulnerability ID', 'CVE', 'Severity', 
        'CVSS Score', 'Summary'
    ])
    
    # Write vulnerability rows
    for vuln in vulnerabilities:
        writer.writerow([
            vuln.get('package', ''),
            vuln.get('version', ''),
            vuln.get('ecosystem', ''),
            vuln.get('id', ''),
            vuln.get('cve', ''),
            vuln.get('severity', ''),
            vuln.get('cvss_score', ''),
            vuln.get('summary', '')
        ])
    
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=vulnerability-report.csv'}
    )
    return response


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    # Print startup banner
    log("=" * 50)
    log(f"{APP_NAME} v{APP_VERSION} - Dependency Vulnerability Scanner")
    log("=" * 50)
    log("Author: Elif Sude ATES")
    log("GitHub: https://github.com/elifsudeates/depshield")
    log("=" * 50)
    
    # Run Flask development server
    # threaded=True enables concurrent request handling for SSE
    app.run(debug=True, port=5000, threaded=True)
