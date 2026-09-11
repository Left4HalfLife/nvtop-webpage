#!/usr/bin/env python3
"""
nvtop Web App - Secure Flask API for monitoring and system actions
"""

import hmac
import json
import os
import re
import secrets
import subprocess
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, request, jsonify, render_template, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
)

CONFIG_PATH = Path(os.environ.get("CONFIG_PATH", "instance/config.json"))
LOG_PATH = Path(os.environ.get("LOG_PATH", "instance/logs/action.log"))
AUTH_TOKEN_HEADER = os.environ.get("AUTH_TOKEN_HEADER", "X-Auth-Token")
ACTION_NAME_PATTERN = re.compile(r"^[a-z0-9_]+$")

with CONFIG_PATH.open(encoding="utf-8") as config_file:
    CONFIG = json.load(config_file)

if not isinstance(CONFIG.get("actions"), dict):
    raise ValueError("config actions must be an object")
for action_name, action in CONFIG["actions"].items():
    command = action.get("command") if isinstance(action, dict) else None
    if not ACTION_NAME_PATTERN.fullmatch(action_name):
        raise ValueError(f"invalid action name: {action_name}")
    if not isinstance(command, list) or not command or not all(
        isinstance(argument, str) and argument for argument in command
    ):
        raise ValueError(f"action {action_name} must have a non-empty command array")
    timeout = action.get("timeout", 30)
    if not isinstance(timeout, int) or not 1 <= timeout <= 300:
        raise ValueError(f"action {action_name} timeout must be between 1 and 300")


def require_auth(function):
    """Require either an authenticated browser session or configured API token."""
    @wraps(function)
    def decorated(*args, **kwargs):
        configured_token = os.environ.get("AUTH_TOKEN", "")
        supplied_token = request.headers.get(AUTH_TOKEN_HEADER, "")
        token_valid = bool(configured_token) and hmac.compare_digest(
            supplied_token, configured_token
        )
        if not session.get("authenticated") and not token_valid:
            return jsonify({"error": "Unauthorized"}), 401
        return function(*args, **kwargs)
    return decorated


# ============== API ENDPOINTS ==============

@app.get('/api/status')
@require_auth
def get_status():
    """Get a one-shot GPU status report."""
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            shell=False,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return jsonify({"error": result.stderr.strip() or "GPU status failed"}), 503
        return jsonify({"output": result.stdout})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "GPU status command timed out"}), 504
    except FileNotFoundError:
        return jsonify({"error": "nvidia-smi is not available"}), 503


@app.get("/healthz")
def healthcheck():
    return jsonify({"status": "ok"})


@app.post("/api/login")
def login():
    credentials = request.get_json(silent=True) or {}
    expected_user = os.environ.get("AUTH_USER", "nvtop-admin")
    expected_password = os.environ.get("AUTH_PASSWORD", "")
    supplied_user = credentials.get("user", "")
    supplied_password = credentials.get("password", "")

    if not expected_password:
        return jsonify({"error": "Authentication is not configured"}), 503
    if not isinstance(supplied_user, str) or not isinstance(supplied_password, str):
        return jsonify({"error": "Invalid credentials"}), 401
    if hmac.compare_digest(supplied_user, expected_user) and hmac.compare_digest(
        supplied_password, expected_password
    ):
        session.clear()
        session["authenticated"] = True
        return jsonify({"message": "Login successful"})
    return jsonify({"error": "Invalid credentials"}), 401


@app.post("/api/logout")
@require_auth
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.post("/api/action/<action_name>")
@require_auth
def run_action(action_name):
    action = CONFIG["actions"].get(action_name)
    if action is None:
        return jsonify({"error": "Action not configured"}), 404

    timestamp = datetime.now(timezone.utc).isoformat()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            action["command"],
            shell=False,
            capture_output=True,
            text=True,
            timeout=action.get("timeout", 30),
            check=False,
        )
    except subprocess.TimeoutExpired:
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(f"{timestamp} action={action_name} result=timeout\n")
        return jsonify({"error": "Action timed out"}), 504
    except (FileNotFoundError, PermissionError) as error:
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(f"{timestamp} action={action_name} result=unavailable\n")
        return jsonify({"error": str(error)}), 503

    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp} action={action_name} result=exit-{result.returncode}\n")
    if result.returncode != 0:
        return jsonify({
            "error": "Action failed",
            "output": result.stdout,
            "stderr": result.stderr,
        }), 500
    return jsonify({
        "message": f"{action_name} completed",
        "output": result.stdout,
    })


@app.get("/")
def index():
    actions = [
        {
            "name": action_name,
            "description": action.get("description", action_name),
        }
        for action_name, action in CONFIG["actions"].items()
    ]
    return render_template("index.html", actions=actions)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
