# Development Setup Guide

## Quick Start (Local Development)

### Prerequisites
- Python 3.10+ installed
- Docker (optional, for container testing)
- pip or poetry

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Setup Configuration
```bash
# Create instance directory
mkdir -p instance/logs

# Copy config example (edit to customize actions)
cp instance/config.json.example instance/config.json

# Edit instance/config.json to add your own action buttons
```

### Step 3: Set Authentication Credentials
Create a `.env` file:
```bash
export AUTH_USER="nvtop-admin"
export AUTH_PASSWORD="your-secret-password-here"
export AUTH_TOKEN_HEADER="X-Auth-Token"
export PORT=5000
```

Or set directly in terminal:
```bash
export AUTH_USER="nvtop-admin"
export AUTH_PASSWORD="mypassword"
export PORT=5000
```

### Step 4: Run Locally
```bash
# Using the run script
./run.sh --auth-user nvtop-admin --auth-password mypassword --port 5000

# Or directly with Python
python app.py
```

The web UI will be available at http://localhost:5000

### Step 5: Test Authentication
1. Open http://localhost:5000 in browser
2. Use `/api/login` endpoint to get a token
3. Include the token in `X-Auth-Token` header for API calls

Example with curl:
```bash
# Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"user":"nvtop-admin","password":"mypassword"}'

# Use returned token in subsequent requests
curl http://localhost:5000/api/status \
  -H "X-Auth-Token: YOUR_TOKEN_HERE"
```

## Adding Custom Actions

### Create Worker Script
1. Create script in `opt/nvtop/actions/`
2. Make executable: `chmod +x script.sh`
3. Define in `instance/config.json`:

```json
{
    "my_custom_action": {
        "description": "My custom action",
        "command": ["opt/nvtop/actions/my_script.sh"],
        "timeout": 60,
        "args": {},
        "requires_restart": false
    }
}
```

### Action Script Template
```bash
#!/bin/bash
set -euo pipefail  # Fail fast for security

# Your action logic here
echo "Action started at $(date)" >> /opt/nvtop/actions/logs/my_action.log

# Example: run a specific command with fixed args
some-command --fixed-arg1 --fixed-arg2

echo "Action completed" >> /opt/nvtop/actions/logs/my_action.log
exit 0
```

## Testing Actions Before Docker

### Test a Single Action
```bash
# From app directory
python3 -c "
import subprocess
from config import CONFIG

action = 'unload_lms'
config = CONFIG['actions'][action]

result = subprocess.run(
    config['command'],
    shell=False,
    capture_output=True,
    text=True,
    timeout=config.get('timeout', 30)
)

print('STDOUT:', result.stdout)
print('STDERR:', result.stderr)
print('Return code:', result.returncode)
"
```

### Test All Actions
```bash
for action_name in "${!CONFIG.actions[@]}"; do
    echo "=== Testing action: $action_name ==="
    # Run test logic here
done
```

## Development Best Practices

### ✅ DO
- Keep `instance/config.json` under git control (not sensitive info)
- Use environment variables for secrets
- Review all subprocess calls with `shell=False`
- Add timeout to all action commands
- Log all actions for audit trail

### ❌ DON'T
- Never use `shell=True`
- Never pass user input to action commands
- Never commit `.env` files
- Never run without authentication in production
- Never use hardcoded passwords

## Common Issues

### Issue: "nvtop binary not found"
```bash
# Solution: Install nvtop or modify command in config.json
pip install python-nvtop  # or use system nvtop
```

### Issue: "Auth token missing from header"
Ensure you're including the auth token when making API calls:
```javascript
// In browser console or client code:
fetch('/api/status', {
    headers: { 'X-Auth-Token': localStorage.getItem('nvtop_auth_token') }
})
```

### Issue: Actions returning 500
1. Check action script has execute permission: `chmod +x /opt/nvtop/actions/*.sh`
2. Review logs in `instance/logs/action.log`
3. Verify command paths exist and are accessible by the nvtop user

## Next Steps

After local testing is complete:
1. Commit your changes (excluding `.env`)
2. Push to repository
3. Build Docker image locally first
4. Deploy with docker-compose or direct docker run

```bash
# Build locally for verification
docker build -t nvtop-webapp .
docker run -p 5000:5000 --rm \
  -e AUTH_USER="nvtop-admin" \
  -e AUTH_PASSWORD="test-password" \
  nvtop-webapp
```

## Debug Mode (Development Only)

For local development with auto-reload:
```bash
FLASK_DEBUG=true python app.py
```

This enables:
- Auto-reload on code changes
- Detailed error pages
- Debug toolbar

⚠️ Never use debug mode in production!
