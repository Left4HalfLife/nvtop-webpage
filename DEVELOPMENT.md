# Development

## Local Run

Local mode uses the host's `nvidia-smi` executable.

```bash
cd nvtop-webpage
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
mkdir -p instance/logs
export AUTH_USER=nvtop-admin
export AUTH_PASSWORD="$(openssl rand -base64 32)"
export SECRET_KEY="$(openssl rand -hex 32)"
./run.sh
```

Open <http://127.0.0.1:5000>. The development server listens on all interfaces,
so use a host firewall or use Docker Compose for stricter local-only binding.

## API Authentication

Browser login uses an HTTP-only session cookie. A command-line client can keep
that cookie:

```bash
curl -c /tmp/nvtop-cookie \
  -H 'Content-Type: application/json' \
  -d '{"user":"nvtop-admin","password":"YOUR_PASSWORD"}' \
  http://127.0.0.1:5000/api/login

curl -b /tmp/nvtop-cookie http://127.0.0.1:5000/api/status
rm -f /tmp/nvtop-cookie
```

Alternatively, set `AUTH_TOKEN` and send it in the `X-Auth-Token` header. Do not
put tokens in URLs.

## Checks

```bash
python3 -m py_compile app.py
python3 -m json.tool instance/config.json >/dev/null
bash -n setup.sh run.sh opt/nvtop/actions/*.sh
NVTOP_AUTH_PASSWORD=test NVTOP_SECRET_KEY=test docker compose config >/dev/null
```

Action commands are read at process startup. Restart the local process or
container after editing `instance/config.json`.