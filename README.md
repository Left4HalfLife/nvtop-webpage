# NVTop Web App - Left4HalfLife Edition

A secure Flask web application that displays nvtop output in a browser with configurable action buttons for GPU management.

## 🎯 Features

- **Live nvtop Display**: Real-time GPU monitoring in your browser
- **Secure Action Buttons**: Configurable bash commands with strict security controls
- **Authentication Required**: All API endpoints require auth tokens
- **Least Privilege**: Runs as dedicated non-root user
- **No Shell Injection**: Direct process calls, fixed arguments only
- **Audit Logging**: All actions are logged for security review

## 🔒 Security Architecture

### Core Principles Implemented:

1. **No Dynamic Shell Building**
   ```python
   # ❌ BAD: Never do this
   exec("bash -c " + userInput)
   
   # ✅ GOOD: Direct subprocess with fixed args
   subprocess.run(["nvtop", "-d"], shell=False, timeout=30)
   ```

2. **No User-Controlled Arguments**
   - Buttons send `{action: "unload_lms"}` only
   - No parameters passed to actions
   - All operations are pre-configured and fixed

3. **Avoid Shell Where Possible**
   ```python
   # ✅ Using argument array, no shell
   subprocess.run(["/opt/actions/unload_lms.sh"], 
                  shell=False, capture_output=True)
   ```

4. **Least Privilege Execution**
   - Docker container runs as `nvtop` user (UID 1000)
   - No sudo/root access in worker scripts
   - Worker scripts run with restricted permissions

5. **Strict Authentication**
   - All `/api/*` endpoints require `X-Auth-Token` header
   - Login endpoint for token acquisition
   - Token stored in memory (not persisted)

## 📋 Files

```
nvtop-webpage/
├── app.py                      # Flask API with auth protection
├── config.py                   # Button-to-command mapping
├── Dockerfile                  # Multi-stage build (builder → minimal runtime)
├── requirements.txt            # Python dependencies
├── run.sh                      # Start script
├── instance/
│   └── config.json.example     # Runtime action configuration (copy to config.json)
└── opt/nvtop/actions/
    ├── unload_lms.sh           # Worker: unload LMS module
    ├── reload_drivers.sh       # Worker: reload GPU drivers
    └── clear_gpu_cache.sh      # Worker: clear GPU cache
```

## 🔧 Configuration

### Authentication (Environment Variables)

```bash
export AUTH_USER="nvtop-admin"
export AUTH_PASSWORD="your-secret-password"
export PORT=5000
export CONFIG_PATH="instance/config.json"
export AUTH_TOKEN_HEADER="X-Auth-Token"
```

### Runtime Configuration (`instance/config.json`)

Copy `config.json.example` to `config.json`:

```json
{
    "log_file": "logs/action.log",
    
    "actions": {
        "unload_lms": {
            "description": "Unload LMS application from GPU",
            "command": ["/opt/nvtop/actions/unload_lms.sh"],
            "timeout": 30,
            "args": {},
            "requires_restart": false
        }
    }
}
```

**⚠️ Security Note**: 
- Action `command` is NEVER overridden by user config (prevents injection)
- Only safe fields like `description`, `timeout` can be overridden

## 🐳 Docker Build & Run

### Build Image

```bash
docker build -t nvtop-webapp .
```

### Run Container

```bash
docker run -d \
  --name nvtop-webapp \
  -p 5000:5000 \
  -e AUTH_USER="nvtop-admin" \
  -e AUTH_PASSWORD="your-password" \
  nvtop-webapp
```

### Access Web UI

Open http://localhost:5000 in your browser. Use `/api/login` to authenticate and get a token, then refresh the page or use the provided auth mechanism.

## 🚀 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy config example (create instance directory first)
mkdir -p instance && cp instance/config.json.example instance/config.json

# Start app
python app.py
# or
./run.sh --auth-user nvtop-admin --auth-password mypassword --port 5000
```

## 📡 API Endpoints

### Authentication

- `POST /api/login` - Authenticate and get token
  ```json
  { "user": "nvtop-admin", "password": "your-secret" }
  ```
  
- `POST /api/logout` - Logout (requires auth)

### GPU Monitoring

- `GET /api/status` - Get current nvtop screen (requires auth)

### Actions

- `POST /api/action/{action_name}` - Run configured action (requires auth)
  ```json
  { "payload": {} }  // Optional args per action definition
  ```

Example: `/api/action/unload_lms`

## ⚙️ Customizing Actions

To add a new action button:

1. Edit `instance/config.json`
2. Add action definition:
```json
{
    "my_action": {
        "description": "Do something cool",
        "command": ["nvtop", "-o", "/tmp/custom.png"],
        "timeout": 30,
        "args": {"mode": "custom"},
        "requires_restart": false
    }
}
```

**⚠️ IMPORTANT**: The `command` field MUST match an actual executable. Do not set to user input.

## 🛡️ Worker Script Template

Create worker scripts in `/opt/nvtop/actions/`:

```bash
#!/bin/bash
set -euo pipefail  # Fail on error, undefined vars, pipe failures

# Your operation here
# Example: restricted operation with fixed path
nvidia-smi some-command --fixed-arg

# Log completion
echo "[$(date)] Operation completed" >> /opt/nvtop/logs/action.log
exit 0
```

Make executable:
```bash
chmod +x /opt/nvtop/actions/your_action.sh
```

## 📝 Logging

All actions are logged to files specified in config. Check `instance/logs/` for audit trail.

## 🔮 Future Enhancements

- [ ] OAuth2 integration
- [ ] Rate limiting on action endpoints
- [ ] Action permission levels (admin/user)
- [ ] Docker compose with dedicated user setup
- [ ] Health check probes for load balancers
