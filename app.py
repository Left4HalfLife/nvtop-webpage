#!/usr/bin/env python3
"""
nvtop Web App - Secure Flask API for monitoring and system actions
"""

import os
import json
from flask import Flask, request, jsonify
import subprocess
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
CONFIG_PATH = os.environ.get('CONFIG_PATH', 'instance/config.json')

# CORS middleware for browser access
from flask_cors import CORS
CORS(app)

with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

AUTH_TOKEN = os.environ.get('AUTH_TOKEN', '')
AUTH_TOKEN_HEADER = os.environ.get('AUTH_TOKEN_HEADER', 'X-Auth-Token')


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get(AUTH_TOKEN_HEADER) or \
                 request.args.get('token') or \
                 request.form.get('token')
        
        if not token or token != AUTH_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


# ============== API ENDPOINTS ==============

@app.route('/api/status', methods=['GET'])
@require_auth
def get_status():
    """Get current nvtop screen output"""
    try:
        result = subprocess.run(
            ["nvtop", "-d"],
            shell=False,
            capture_output=True,
            text=True,
            timeout=CONFIG.get('timeout', 30) if 'status' in CONFIG['actions'] else 10
        )
        
        return jsonify({
            "output": result.stdout,
            "stderr": result.stderr if result.returncode != 0 else ""
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Command timed out"}), 504
    except FileNotFoundError:
        return jsonify({"error": "nvtop binary not found - is it installed?"}), 500
    except Exception as e:
        app.logger.exception("Failed to get nvtop status")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/action/<action_name>', methods=['POST'])
@require_auth
def run_action(action_name):
    """Run a configured action"""
    from datetime import datetime
    
    action_config = CONFIG['actions'].get(action_name)
    
    if not action_config:
        return jsonify({"error": f"Action '{action_name}' not configured"}), 404
    
    try:
        # Log action execution for audit
        log_entry = f"{datetime.now().isoformat()} | Action: {action_name}"
        log_path = CONFIG.get('log_file', 'instance/logs/action.log')
        os.makedirs(os.path.dirname(log_path) or '.', exist_ok=True)
        with open(log_path, 'a') as log_f:
            log_f.write(log_entry + '\n')
        
        # Run the command - NEVER with shell, fixed arguments only
        result = subprocess.run(
            action_config['command'],
            shell=False,  # CRITICAL: Never use shell=True
            capture_output=True,
            text=True,
            timeout=action_config.get('timeout', 60)
        )
        
        if result.returncode == 0:
            return jsonify({
                "success": True,
                "message": action_name + " completed",
                "output": result.stdout
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Action failed with code {result.returncode}",
                "output": result.stdout,
                "stderr": result.stderr
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Action '{action_name}' timed out"}), 504
    except Exception as e:
        app.logger.exception("Failed to run action '%s'", action_name)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate and get a token"""
    user = request.json.get('user', '') if request.is_json else ''
    password = request.form.get('password', '')
    
    expected_user = os.environ.get('AUTH_USER', 'nvtop-admin')
    expected_pass = os.environ.get('AUTH_PASSWORD', '')
    
    if user == expected_user and password == expected_pass:
        token = secrets.token_urlsafe(32)
        app.secret_token = token
        return jsonify({
            "token": token,
            "message": "Login successful"
        })
    
    return jsonify({"error": "Invalid credentials"}), 401


@app.route('/api/logout', methods=['POST'])
@require_auth
def logout():
    """Logout and invalidate token"""
    app.secret_token = None
    return jsonify({"message": "Logged out successfully"})


# ============== HTML TEMPLATES ==============

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NVTop Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #1a1a2e; color: #eee; font-family: 'Courier New', monospace; padding: 20px; }
        h1 { color: #4ecca3; margin-bottom: 20px; }
        .screen { background: #0f0f23; border: 2px solid #4ecca3; border-radius: 8px; padding: 15px; height: 60vh; overflow: auto; white-space: pre-wrap; font-size: 12px; line-height: 1.4; }
        .actions { margin-top: 20px; display: grid; gap: 10px; }
        button { background: #4ecca3; color: #1a1a2e; border: none; padding: 12px 20px; font-size: 14px; font-weight: bold; cursor: pointer; border-radius: 4px; transition: all 0.2s; }
        button:hover { background: #3db892; }
        .status { margin-top: 10px; padding: 10px; border-radius: 4px; display: none; }
        .status.success { background: #2d5a27; display: block; }
        .status.error { background: #8b2727; display: block; }
    </style>
</head>
<body>
    <h1>🔌 NVTop Monitor - Left4HalfLife Edition</h1>
    <div id="screen" class="screen">Initializing...</div>
    <div id="status" class="status"></div>

    <script>
        const screen = document.getElementById('screen');
        const status = document.getElementById('status');
        
        async function refreshScreen() {
            try {
                const response = await fetch('/api/status', { headers: { 'X-Auth-Token': getAuthHeader() } });
                if (!response.ok) throw new Error('Failed');
                const data = await response.json();
                screen.textContent = data.output || '';
            } catch (e) { screen.textContent = 'Error: ' + e.message; }
        }
        
        async function runAction(actionName) {
            status.className = 'status';
            status.style.display = 'block';
            try {
                const response = await fetch('/api/action/' + actionName, {
                    headers: { 'X-Auth-Token': getAuthHeader(), 'Content-Type': 'application/json' },
                    method: 'POST', body: '{}'
                });
                const data = await response.json();
                if (response.ok) {
                    status.className = 'status success';
                    status.textContent = '✓ ' + (data.message || actionName + ' completed');
                    setTimeout(refreshScreen, 1000);
                } else {
                    throw new Error(data.error || 'Failed');
                }
            } catch (e) { status.className = 'status error'; status.textContent = '✗ ' + e.message; }
        }
        
        function getAuthHeader() { return window.localStorage.getItem('nvtop_auth_token') || ''; }
        
        refreshScreen(); setInterval(refreshScreen, 100);

        <!-- Action buttons injected below -->
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """Render the main HTML page with config-injected actions"""
    actions_html = ''
    for action_name, action_config in CONFIG['actions'].items():
        if action_name == 'status':
            continue
        
        actions_html += f'<div><button onclick="runAction(\'{action_name}\')">⚡ {action_config.get("description", action_name)}</button></div>'
    
    return HTML_TEMPLATE.replace('<!-- Action buttons injected below -->', actions_html)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"Starting nvtop web app on port {port}")
    print(f"Auth token: {'SET' if AUTH_TOKEN else 'NOT SET (use /api/login)'}")
    app.run(host='0.0.0.0', port=port, debug=debug)
