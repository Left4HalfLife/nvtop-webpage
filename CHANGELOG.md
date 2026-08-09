# Changelog

All notable changes to nvtop-webpage.

## [Unreleased]

### Added
- Initial implementation with Flask web application
- Secure authentication middleware for all API endpoints
- Action button system with fixed command templates
- Multi-stage Docker build (builder → minimal runtime)
- Non-root execution environment (least privilege)
- Audit logging for all action executions
- Worker script framework in `/opt/nvtop/actions/`

### Security Features
- No shell=True anywhere in the codebase
- Direct subprocess calls with argument arrays
- Authentication required on all /api/* endpoints
- Hardcoded command templates cannot be overridden via config
- Non-root Docker user (nvtop, UID 1000)
- Secure secrets management via environment variables
- Audit trail for incident response

### Files Created
- `app.py` - Flask API application with auth protection
- `config.py` - Action-to-command mapping with security boundaries
- `Dockerfile` - Multi-stage build instructions
- `docker-compose.yml` - Container orchestration
- `requirements.txt` - Python dependencies
- `run.sh` - Development start script
- `.env.example` - Environment variable template
- `setup.sh` - Container setup helper
- `Makefile` - Common tasks automation
- `README.md` - User documentation
- `DEVELOPMENT.md` - Developer guide
- `SECURITY.md` - Security checklist and hardening
- `ARCHITECTURE.md` - System architecture overview
- `.dockerignore` - Docker build exclusions
- `.github/workflows/ci.yml` - CI/CD pipeline

### Worker Scripts
- `opt/nvtop/actions/unload_lms.sh` - Unload LMS GPU modules
- `opt/nvtop/actions/reload_drivers.sh` - Reload NVIDIA drivers
- `opt/nvtop/actions/save_state.sh` - Capture nvtop screenshots
- `opt/nvtop/actions/clear_gpu_cache.sh` - Clear GPU memory

### Configuration Files
- `instance/config.json` - Runtime action definitions
- `instance/logs/` - Audit log directory (gitignored)

### Next Steps
- Add comprehensive unit tests for security checks
- Implement OAuth2 integration
- Add rate limiting on API endpoints
- Create health check probes for load balancers
- Document specific GPU management commands for Left4HalfLife
