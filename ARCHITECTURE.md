# Architecture Overview - nvtop-webpage

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Web Browser                           │
│              (User Interface Layer)                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │    /api/status  → Live nvtop screen display       │   │
│  │    /api/action/{name}  → Execute configured cmd   │   │
│  │    /api/login, /api/logout  → Auth management     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                      ↑ HTTPS (optional)
                      ↓ HTTP:80 → API:5000
┌─────────────────────────────────────────────────────────┐
│              Flask Application Layer                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │  app.py                                          │   │
│  │  • Authentication middleware                     │   │
│  │  • API endpoints (status, actions, login)        │   │
│  │  • HTML template rendering                       │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  config.py                                       │   │
│  │  • Action-to-command mapping                     │   │
│  │  • Security-enforced command definitions         │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                      ↓ subprocess calls (shell=False)
┌─────────────────────────────────────────────────────────┐
│              Worker Script Layer                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  /opt/nvtop/actions/*.sh                         │   │
│  │  • unload_lms.sh  → Unload GPU modules           │   │
│  │  • reload_drivers.sh → Reload GPU drivers        │   │
│  │  • clear_gpu_cache.sh → Clear memory cache       │   │
│  │  • All scripts run as non-root user              │   │
│  └──────────────────────────────────────────────────┘   │
│  • Each script runs in isolated filesystem scope        │
│  • No inter-process communication with other actions    │
└─────────────────────────────────────────────────────────┘
```

## Security Architecture Layers

### Layer 1: Authentication
```
Request → /api/* endpoint
         ↓
   require_auth() decorator
         ↓
   Validate X-Auth-Token header
         ↓
   Compare with AUTH_TOKEN env var
         ↓
   [VALID] → Process request
   [INVALID] → 401 Unauthorized
```

### Layer 2: Command Execution
```
User clicks button → sends {"action": "unload_lms"}
                   ↓
          Flask receives POST /api/action/unload_lms
                   ↓
     Lookup in config.py actions["unload_lms"]
                   ↓
   EXECUTION TEMPLATE (hardcoded, NEVER modified by user):
   ["/opt/nvtop/actions/unload_lms.sh", shell=False]
                   ↓
        subprocess.run() with fixed argument array
                   ↓
        NO shell interpretation possible
```

### Layer 3: Process Isolation
```
Worker script runs as:
  • User: nvtop (UID 1000) - non-root
  • GID: nvtop (GID 1000)
  • Working directory: /opt/nvtop/actions/
  
Filesystem boundaries:
  • Read-only: actions scripts, config.json
  • Writable: logs/ directory only
  • No access to /etc, /root, or sensitive paths
```

### Layer 4: Audit Trail
```
All actions logged to instance/logs/action.log with format:
  [2026-07-29T16:43:43] | Action: unload_lms | Exit code: 0
  
Security review capability:
  • Track which actions ran
  • Identify patterns (e.g., rapid action execution)
  • Review before/after states via logs
```

## Attack Surface Analysis

### Vulnerable Patterns (NOT implemented):
- ❌ `exec(userInput)` → Dynamic command execution
- ❌ `os.system()` → Shell interpretation
- ❌ User-controlled file paths → Path traversal
- ❌ Environment variable injection → Command override
- ❌ Running as root → Elevated privilege abuse

### Protected Implementations:
```python
# SAFE: Fixed arguments, no shell
subprocess.run(["nvtop", "-d"], shell=False)

# SAFE: Direct script call
subprocess.run(["/opt/nvtop/actions/unload_lms.sh"], 
               shell=False)

# SAFE: Authentication enforced
@require_auth  # All API endpoints require valid token

# SAFE: Non-root execution
USER nvtop runs all worker scripts
```

## Configuration Security

### instance/config.json (runtime config):
- ✅ Can override action descriptions (informational only)
- ❌ CANNOT override command paths or arguments (security boundary)
- ⚠️ Never contains secrets (AUTH_TOKEN, passwords)

### Environment Variables (production values):
- AUTH_USER="nvtop-admin" (non-root user for login)
- AUTH_PASSWORD="your-secret-password" (user must know this)
- AUTH_TOKEN_HEADER="X-Auth-Token" (header name)
- CONFIG_PATH="instance/config.json" (config location)

### Docker Security:
```dockerfile
FROM python:3.11-slim AS runtime  # Minimal base image

# Create dedicated user
RUN groupadd --gid 1000 nvtop \
    && useradd --uid 1000 --gid 1000 nvtop

USER nvtop  # Drop privileges before running app
```

## Deployment Checklist

### Pre-deployment:
- [ ] AUTH_PASSWORD set to strong value (min 16 chars, mixed case)
- [ ] All action scripts have correct paths and are executable
- [ ] instance/config.json has reviewed commands
- [ ] .env file excluded from git (contains secrets)
- [ ] Log directory writable by nvtop user

### Post-deployment:
- [ ] Verify authentication works (`/api/login` endpoint)
- [ ] Test each action returns expected output
- [ ] Review logs for unauthorized access attempts
- [ ] Configure HTTPS via reverse proxy (nginx/caddy)
- [ ] Set up monitoring for anomaly detection

## Incident Response Matrix

### Unauthorized API Access Detected:
1. **Immediate**: Stop container, review logs
2. **Short-term**: Reset AUTH_PASSWORD, audit action scripts
3. **Long-term**: Review CI/CD pipeline, update secrets rotation

### Suspicious Action Execution:
1. **Log entry** will show action name and timestamp
2. **Worker script** logs its execution
3. **Investigate**: Compare before/after system state
4. **Mitigate**: Update config.json if command was modified

## Compliance Notes

- ✅ Data minimization: Only GPU status data collected
- ✅ Principle of least privilege: Non-root, minimal permissions
- ✅ Audit trails: All actions logged with timestamps
- ✅ Defense in depth: Multiple layers (auth, process isolation, filesystem)
- ✅ Fail securely: Default timeouts, restrictive file permissions
