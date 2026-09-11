# Changelog

## Unreleased

### Changed

- Simplified setup to `./setup.sh` followed by `docker compose up -d`.
- Added browser session login and optional API-token authentication.
- Protected GPU status and action endpoints.
- Added an unauthenticated `/healthz` endpoint for container probes.
- Bound the default deployment to localhost and required generated secrets.
- Added a read-only container filesystem, dropped capabilities, and writable
  audit-log mount.
- Replaced nonfunctional privileged GPU actions with a safe example action.
- Updated the dashboard to use a one-shot `nvidia-smi` status report.