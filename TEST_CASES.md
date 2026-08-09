# Test Cases - NVTop Webpage Docker Networking & Security

## Overview
This document contains test cases to verify proper Docker networking, CORS configuration, 
and security boundaries in the nvtop-webpage application.

## Test Case 1: Host Network Accessibility (Docker Compose)

### Scenario: Container needs to reach host services
**Test Command:**
```bash
# Inside docker-compose setup
docker exec nvtop-webapp curl -I http://localhost:8080/  # Replace with actual port
```

**Expected Result:** 
- Can access internal containers on localhost
- Host services must use `host.docker.internal`

**Configuration:**
```yaml
# In instance/config.json
"unload_comfyui": {
    "command": ["curl", "-X", "POST", "${COMFY_UI_URL:-http://host.docker.internal:17493}/models/unload"]
}
```

### Test: Verify host.docker.internal resolution
```bash
docker exec -it nvtop-webapp bash
root@nvtop-webapp:/app# curl http://host.docker.internal/
# Should resolve to host machine IP
root@nvtop-webapp:/app# ping google.com  # Network connectivity test
```

**Potential Issue:** `localhost` inside Docker refers to container, not host!
**Solution:** Use environment variable or hardcoded URL in command.

---

## Test Case 2: CORS Configuration

### Scenario: Browser makes requests from port 80/443 to app on :5000
**Test Command:**
```bash
# Test from browser console (Chrome DevTools)
fetch('/api/login', {
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
    body: JSON.stringify({user: "test", password: "secret"})
}).then(r => r.json()).then(console.log)
```

**Expected Result:**
- Browser accepts GET/POST requests to /api/*
- No mixed content warnings if HTTPS or same origin
- Response headers include `Access-Control-Allow-Origin`

### Test: Check CORS headers
```bash
curl -v http://localhost:5000/api/status \
  -H "Origin: http://example.com" | grep -i "access-control"
```

**Expected Header:**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: X-Auth-Token, Content-Type
```

### Issue to Fix: If CORS headers missing in response
Add explicit middleware:
```python
from flask_cors import CORS

CORS(app, origins=["http://localhost:80"], methods=["GET", "POST"])
# Or for all origins (less secure):
CORS(app)
```

---

## Test Case 3: Authentication Flow

### Scenario: Verify auth token is enforced and stored client-side
**Test Sequence:**
```bash
# Step 1: Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"user":"nvtop-admin","password":"secret"}'

# Expected: {"token": "abc123...", "message": "Login successful"}

# Step 2: Use token in subsequent requests
TOKEN=$(curl -s -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"user":"nvtop-admin","password":"secret"}' | jq -r '.token')

# Step 3: Access protected endpoint
curl -X GET http://localhost:5000/api/status \
  -H "X-Auth-Token: $TOKEN"

# Should return nvtop output
```

### Test: Unauthorized access blocked
```bash
# Without token - should fail with 401
curl -v http://localhost:5000/api/status | grep "< HTTP/1.1 401"
```

**Expected Result:**
- Response code 401 Unauthorized
- Body: `{"error": "Unauthorized"}`

---

## Test Case 4: Action Execution (Security Boundary)

### Scenario: Verify action commands execute with fixed arguments only
**Test Command for Each Action:**
```bash
# Test unload_all_lm_models
curl -X POST http://localhost:5000/api/action/unload_all_lm_models \
  -H "X-Auth-Token: $TOKEN" | jq .

# Expected in response.output:
# "Loaded models unloaded successfully"
# or stderr with any errors (non-fatal)
```

### Test: Verify no shell interpretation
```bash
# Try injecting command via action name - should fail gracefully
curl -X POST http://localhost:5000/api/action/../../../etc/passwd \
  -H "X-Auth-Token: $TOKEN"

# Expected: {"error": "Action '...' not configured"} with 404
```

**Security Check:** Action names are dictionary keys, not shell arguments!

---

## Test Case 5: Docker Compose Network Isolation

### Scenario: App needs to talk to host services (LM Studio, ComfyUI)
**Setup:**
```yaml
version: '3.8'
services:
  nvtop-webapp:
    build: .
    ports:
      - "5000:5000"
    environment:
      - COMFY_UI_URL=http://host.docker.internal:17493
    volumes:
      - ./instance:/app/instance:ro
    
  lm-studio:
    image: lmstudio/lmstudio:latest
    ports:
      - "1240:1240"
    networks:
      - app-network

  comfyui:
    # Your ComfyUI service
    networks:
      - app-network
    
networks:
  app-network:
```

### Test: Internal container communication
```bash
# From within nvtop-webapp container
docker exec nvtop-webapp bash
root@nvtop-webapp:/app# curl http://lm-studio:1240/api/  # Replace with internal service name
# Should connect to sibling container
```

**Issue:** If services not in same network, use DNS or port mapping.

---

## Test Case 6: Filesystem Boundaries

### Scenario: Worker scripts cannot access sensitive paths
**Test Command:**
```bash
docker exec nvtop-webapp bash
root@nvtop-webapp:/app# cat /etc/passwd
# Should fail - EACCES or ENOENT
```

### Test: Verify worker script permissions
```bash
docker exec nvtop-webapp ls -la /opt/nvtop/actions/
# Expected: drwxr-x--- nvtop:nvtop 700
#          -rwxr-x--- nvtop:nvtop 644 unload_lms.sh
```

**Expected:** Scripts readable but only executable by nvtop user.

---

## Test Case 7: Timeout Enforcement

### Scenario: Action times out after configured duration
**Test Command:**
```bash
# Configure a slow action
echo '{"timeout": 5}' > instance/config.json

curl -v -X POST http://localhost:5000/api/action/slow_action \
  -H "X-Auth-Token: $TOKEN" | grep "timed out"
```

**Expected:** Response with 504 status and "timed out" error message.

---

## Test Case 8: Mixed Content (HTTPS Issues)

### Scenario: Port 5000 over HTTP, browser on HTTPS
**Issue:** Browser blocks `http://localhost:5000` requests from HTTPS page
**Solution Options:**

1. **Use reverse proxy with TLS termination:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. **Accept HTTP in development (for local testing only):**
   - Disable strict mixed content warnings in browser
   - Or configure `FLASK_ENV=development` with relaxed CORS

---

## Test Case 9: Environment Variable Injection Prevention

### Scenario: Verify commands don't interpret environment variables
**Test Command:**
```bash
# Set malicious environment variable
export PATH="/bin:/malicious/path"
export LD_PRELOAD="/etc/passwd"

# Run app - commands should use fixed paths
python app.py &

curl http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"user":"nvtop-admin","password":"test"}'
```

**Expected:** Actions use `command` array from config, not PATH
Result: Fixed paths like `["curl", "-X", "POST", "..."]` are used directly.

---

## Test Case 10: Audit Log Verification

### Scenario: All actions logged for security review
**Test Command:**
```bash
docker exec nvtop-webapp bash
root@nvtop-webapp:/app# cat instance/logs/action.log
```

**Expected Output Format:**
```
[2026-07-31T14:30:45.123456+10:00] | Action: unload_all_lm_models
[2026-07-31T14:35:12.789012+10:00] | Action: load_small_creative
```

**Verify:** Each action has timestamp and action name for audit trail.

---

## Quick Test Script (run from host)

Save as `test_nvtop.sh`:
```bash
#!/bin/bash
set -e

BASE_URL="${BASE_URL:-http://localhost:5000}"
TOKEN=""

echo "=== NVTop Webpage Security Tests ==="
echo ""

# Helper function
test_request() {
    local method=$1
    local path=$2
    shift 2
    local args=("$@")
    
    if [ -n "$TOKEN" ]; then
        local headers="-H 'X-Auth-Token: $TOKEN'"
    else
        local headers=""
    fi
    
    echo "Testing: $method $path ..."
    curl -s${headers} "${BASE_URL}${path}" "${args[@]}" | jq . 2>/dev/null || echo ""
    echo ""
}

# Test 1: No auth fails on protected endpoint
echo "--- Test 1: Authentication Required ---"
test_request GET "/api/status"

# Login
echo "--- Test 2: Login ---"
LOGIN=$(curl -s -X POST "$BASE_URL/api/login" \
  -H "Content-Type: application/json" \
  -d '{"user":"nvtop-admin","password":"secret"}')
TOKEN=$(echo $LOGIN | jq -r '.token')
echo "Got token: ${TOKEN:0:16}..."
echo ""

# Test 3: Authenticated access works
echo "--- Test 3: Authenticated Status ---"
test_request GET "/api/status"

# Test 4: Action execution
echo "--- Test 4: Action Execution ---"
test_request POST "/api/action/check_loaded_models"

echo "=== All Tests Complete ==="
```

Run with: `bash test_nvtop.sh`

---

## Summary of Issues to Address

| Issue | Impact | Fix Status |
|-------|--------|------------|
| `localhost` vs `host.docker.internal` | ComfyUI may not be reachable | ✅ Fixed in config.json |
| CORS headers missing | Browser blocks requests | ⏳ Need flask-cors import |
| Mixed content (HTTP/HTTPS) | Browser security warnings | Documentation added |
| Audit logs location | Logs may not persist | Fixed to `instance/logs/action.log` |

## Running All Tests

```bash
# Install jq if not present
sudo apt install jq  # Ubuntu/Debian

# Run test script
bash test_nvtop.sh

# Or individual tests
docker exec nvtop-webapp ping -c 3 google.com
docker exec nvtop-webapp curl http://localhost:5000/api/status
```
