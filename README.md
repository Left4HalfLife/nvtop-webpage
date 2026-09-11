# NVTop Web App

An authenticated web dashboard for NVIDIA GPU status. It displays a one-shot
`nvidia-smi` report and can expose administrator-defined action buttons without
invoking a shell.

## Requirements

- Linux with a working NVIDIA driver
- Docker with the Compose plugin
- NVIDIA Container Toolkit configured for Docker

Confirm GPU access before setup:

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu24.04 nvidia-smi
```

## Setup

```bash
cd nvtop-webpage
chmod +x setup.sh
./setup.sh
docker compose up -d
```

The setup script creates `.env` with random credentials, prepares the audit-log
directory, and builds the image. Display the generated username and password:

```bash
grep '^NVTOP_AUTH_' .env
```

Open <http://127.0.0.1:5001> and log in. Check startup status with:

```bash
docker compose ps
docker compose logs --tail=100 nvtop-webapp
```

Stop the app with:

```bash
docker compose down
```

## Action Buttons

Actions are defined in `instance/config.json`. Commands must be argument arrays;
they are executed directly with `shell=False` and receive no browser-supplied
arguments.

```json
{
  "actions": {
    "list_gpus": {
      "description": "List GPUs",
      "command": ["nvidia-smi", "-L"],
      "timeout": 10
    }
  }
}
```

The configuration file is trusted administrator input. Anyone who can edit it
can execute commands as the container's `nvtop` user. Restart after changing it:

```bash
docker compose restart nvtop-webapp
```

Scripts placed in `opt/nvtop/actions/` appear at the same path inside the
container. They must be executable and use programs installed in the image.

## Security

- Compose binds the app to `127.0.0.1`; it is not exposed to the LAN by default.
- API status and action endpoints require a login session or `X-Auth-Token`.
- The container runs as UID 1000, drops Linux capabilities, and has a read-only
  root filesystem. Only `instance/logs/` is writable.
- Do not mount the Docker socket, add `privileged: true`, or grant kernel-module
  capabilities to the web app.
- Use an authenticated HTTPS reverse proxy before allowing remote access.
- Never commit `.env`; it contains the login password and session secret.

For optional local development and API examples, see `DEVELOPMENT.md`. For the
deployment threat model, see `SECURITY.md`.

## Troubleshooting

`no matching device driver` or `could not select device driver` means NVIDIA
Container Toolkit is missing or not configured for Docker.

`nvidia-smi is not available` means the NVIDIA runtime did not inject its tools
into the container. Re-run the GPU-access check from the Requirements section.

If the container cannot write the audit log:

```bash
mkdir -p instance/logs
chmod 700 instance/logs
```