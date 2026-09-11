# Security

## Trust Model

The browser may select only an action name. The corresponding command and
arguments come from the administrator-managed `instance/config.json` and run
with `shell=False`. Treat that file and `opt/nvtop/actions/` as executable code.

The application runs as the non-root `nvtop` user. Docker Compose drops all
Linux capabilities, blocks privilege escalation, mounts the application
filesystem read-only, and publishes only to `127.0.0.1`.

## Deployment Checklist

- Keep `.env` readable only by its owner (`chmod 600 .env`).
- Use long random values for `NVTOP_AUTH_PASSWORD` and `NVTOP_SECRET_KEY`.
- Review every command in `instance/config.json` before restarting.
- Keep action scripts owned and writable only by an administrator.
- Put an authenticated HTTPS reverse proxy in front of the app for remote use.
- Back up and review `instance/logs/action.log`.
- Keep Flask, Gunicorn, the base image, Docker, and NVIDIA tooling updated.

## Do Not

- Do not set `shell=True` or construct shell command strings.
- Do not accept command arguments, paths, or environment variables from API
  requests.
- Do not mount `/var/run/docker.sock` into this container.
- Do not run the container as root or privileged.
- Do not grant capabilities for driver reloads or kernel-module management.
- Do not expose port 5001 directly to an untrusted network.

Privileged GPU reset and driver management do not belong in this web process.
Use a separately audited host service with a narrow interface if those features
are required.

## Incident Response

```bash
docker compose down
cp instance/logs/action.log "incident-$(date +%s).log"
```

Replace the password and secret in `.env`, review configured actions and logs,
then rebuild before restarting.