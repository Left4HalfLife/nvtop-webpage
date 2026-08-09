# Security Checklist - NVTop Webpage Deployment

## ✅ Implemented Security Controls

### 1. No Shell Injection
- ✅ All subprocess calls use `shell=False`
- ✅ Commands are argument arrays, not strings
- ✅ No user input in command construction

### 2. Authentication
- ✅ `/api/status` requires auth token
- ✅ `/api/action/*` requires auth token  
- ✅ Login endpoint for secure token acquisition
- ✅ Token stored only in memory (not persisted)

### 3. Least Privilege
- ✅ Docker container runs as non-root user (`nvtop`, UID 1000)
- ✅ Worker scripts run with restricted permissions
- ✅ No sudo/root execution paths

### 4. Input Validation
- ✅ Actions have fixed command templates
- ✅ No parameter passing to actions
- ✅ All operations pre-configured at startup

### 5. Audit Logging
- ✅ Every action logged with timestamp
- ✅ Logs stored in isolated directories
- ✅ Accessible for security review

## 🔒 Before Production Deployment

### Required Configuration:

1. **Set Strong Authentication**
```bash
export AUTH_PASSWORD="strong-secure-password-min-8-chars"
export AUTH_USER="nvtop-admin"
```

2. **Review Action Commands**
- ✅ Ensure all paths in `instance/config.json` are correct
- ✅ Test each action locally before deployment
- ❌ NEVER use wildcards or user-controlled paths

3. **Network Security**
```bash
# Only expose port 5000, not debug endpoints
docker run -p 5000:5000 nvtop-webapp
```

4. **Enable HTTPS (Recommended)**
- Use a reverse proxy (nginx/caddy) with SSL/TLS
- Or configure Flask to use Let's Encrypt

### Security Hardening Steps:

```bash
# 1. Set restrictive permissions on action scripts
chmod 750 /opt/nvtop/actions/*.sh
chown nvtop:nvtop /opt/nvtop/actions

# 2. Make log files readable only by owner  
chmod 640 /app/logs/*
chown nvtop:nvtop /app/logs

# 3. Drop unnecessary capabilities in Dockerfile:
# FROM scratch -> use specific base image
# RUN ["/bin/bash", "-c", "cap_drop ALL && cap_add NET_BIND_SERVICE"]
```

### Runtime Monitoring:

```bash
# Monitor for unauthorized API access
watch -n 60 'docker logs nvtop-webapp --tail 100'

# Check action execution frequency
tail -f instance/logs/action.log | grep "completed"

# Review failed attempts
grep "error\|Error" instance/logs/*.log
```

## 🚫 Security Anti-Patterns to Avoid

- ❌ Never change `shell=True` in any subprocess call
- ❌ Never accept URL/path parameters for actions  
- ❌ Never use environment variables in command strings
- ❌ Never commit `.env` or `instance/config.json` (contains secrets)
- ❌ Never run container as root

## 📋 Security Review Commands

```bash
# Check running container user
docker exec nvtop-webapp whoami

# Verify no root processes
docker exec nvtop-webapp ps -u | grep root

# Test authentication (should fail without token)
curl -v http://localhost:5000/api/status

# Review action logs
docker exec nvtop-webapp cat /app/instance/logs/action.log
```

## 🛡️ Incident Response

If suspicious activity detected:

1. **Immediate Actions**
```bash
docker stop nvtop-webapp
docker rm nvtop-webapp
```

2. **Forensics**
```bash
# Review logs
cat instance/logs/*.log > incident_$(date +%s).log

# Check for modified action scripts
git status
diff -r .github/ /opt/nvtop/actions/ 2>/dev/null || true
```

3. **Rebuild with Clean State**
```bash
docker build --pull --rm -f Dockerfile \
  -t nvtop-webapp:clean .
docker rm nvtop-webapp
docker run -d --name nvtop-webapp -p 5000:5000 nvtop-webapp:clean
```

## 📜 Compliance Notes

- All actions are logged for audit trails
- No data exfiltration paths (no network out except API)
- Least privilege principle enforced at multiple layers
- Authentication prevents unauthorized access
- Attack surface minimized (static endpoints only)
