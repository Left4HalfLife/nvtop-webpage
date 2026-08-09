#!/usr/bin/env python3
"""
Configuration module - Button to bash command mapping

Security principles:
- No shell=True ever
- No user-controlled arguments  
- Fixed commands with fixed paths
- Each action runs in isolated environment
"""

import os
import json

CONFIG_PATH = os.environ.get('CONFIG_PATH', 'instance/config.json')

# Default configuration (can be overridden by instance/config.json)
DEFAULT_CONFIG = {
    "log_file": "logs/action.log",
    
    # Action definitions
    # Each action must have:
    # - command: list of arguments (NEVER a shell command string)
    # - timeout: max execution time in seconds
    # Optional: description, requires_restart, etc.
    
    "actions": {
        # Load nvtop screen capture (nvtop default behavior)
        "status": {
            "description": "Refresh nvtop display", 
            "command": ["bash", "-c", "/opt/nvtop/scripts/capture.sh"],  # Fixed path, fixed args
            "timeout": 10,
        },
        
        # Unload LMS module (if configured)
        "unload_lms": {
            "description": "Unload LMS application",
            "command": ["/opt/actions/unload_lms.sh"],  # Direct script call, no shell
            "timeout": 30,
            "requires_restart": False,
        },
        
        # Reload GPU drivers
        "reload_drivers": {
            "description": "Reload NVIDIA drivers",
            "command": ["/opt/actions/reload_drivers.sh"],
            "timeout": 60,
            "requires_restart": True,
        },
        
        # Save nvtop state to file
        "save_state": {
            "description": "Save current screen as image",
            "command": ["/usr/bin/env", "nvtop", "-s", "/tmp/nvtop.png"],
            "timeout": 30,
        },
        
        # Clear GPU cache (careful with data loss!)
        "clear_cache": {
            "description": "Clear GPU memory cache",
            "command": ["/opt/actions/clear_gpu_cache.sh"],
            "timeout": 45,
            "requires_admin": True,  # Additional security flag
        },
        
        # Reset nvtop config (safe operation)
        "reset_config": {
            "description": "Reset nvtop to defaults",
            "command": ["/usr/bin/env", "nvtop", "-r"],
            "timeout": 10,
        },
    }
}


def load_config(config_path=None):
    """Load configuration from file or return defaults"""
    if config_path and os.path.exists(config_path):
        with open(config_path) as f:
            user_config = json.load(f)
        
        # Merge with defaults, user config takes precedence for actions
        merged = {
            "log_file": user_config.get("log_file", DEFAULT_CONFIG["log_file"]),
            "actions": DEFAULT_CONFIG["actions"]
        }
        
        # Allow overriding action descriptions but NOT commands (security)
        if "actions" in user_config:
            for action_name, action_def in DEFAULT_CONFIG["actions"].items():
                if action_name in user_config["actions"]:
                    user_action = user_config["actions"][action_name]
                    merged["actions"][action_name] = {
                        # Keep original command (never override!)
                        "command": action_def.get("command"),
                        "timeout": user_action.get("timeout", action_def.get("timeout")),
                        "description": user_action.get("description", action_def.get("description")),
                        # Only allow certain safe overrides
                        "requires_restart": user_action.get(
                            "requires_restart", 
                            action_def.get("requires_restart", False)
                        ),
                    }
        
        return merged

# Validate and load config at import time  
CONFIG = load_config(CONFIG_PATH)
