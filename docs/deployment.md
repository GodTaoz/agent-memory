# Deployment Guide

This document focuses on practical deployments that are already supported by the repository.

## 1. Local Linux host

```bash
git clone https://github.com/GodTaoz/agent-memory.git
cd agent-memory
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[all]'
cp config/config.example.yaml config/config.yaml
```

Run the REST/admin service:

```bash
export REDIS_HOST=127.0.0.1
uvicorn memory_mcp.main:create_app --factory --host 0.0.0.0 --port 5678
```

Run the MCP stdio service:

```bash
# uses the same Redis/config setup as the REST runtime
export REDIS_HOST=127.0.0.1
memory-mcp-stdio
```

## 2. Docker Compose

```bash
cp config/config.example.yaml config/config.yaml
cp config/permissions.example.yaml config/permissions.yaml
export REDIS_PASSWORD='your-redis-password'
docker-compose up -d
```

Endpoints:

- admin panel: `http://localhost:5678/`
- health: `http://localhost:5678/api/v1/health`

## 3. NAS / home server

Recommended approach:

1. run Redis on the NAS or a trusted LAN host
2. keep `config/config.yaml` and `config/permissions.yaml` under backed-up storage
3. run the REST/admin service behind a reverse proxy if accessed beyond the LAN
4. expose stdio MCP only to local agent processes on the host that needs it

## Data and state paths

By default the service persists local admin state in two places:

- `data/admin_auth.json` relative to the project root
- `data/api_keys.json` relative to the project root
- `data/admin_logs.db` relative to the current working directory

Redis stores the memory records and indexes.

## Backup / restore

### Back up Redis

Use your normal Redis snapshot or AOF strategy. For simple local setups, at minimum archive Redis persistence files on a schedule.

### Back up local admin state

Archive these files together:

```text
data/admin_auth.json
data/api_keys.json
data/admin_logs.db
config/config.yaml
config/permissions.yaml
```

### Restore

1. restore Redis persistence data
2. restore the `data/` files and `config/` files
3. restart the service
4. verify with `/api/v1/health` and an admin login

## Operator checklist

- set a strong admin password immediately after first login
- rotate managed API keys periodically
- restrict network access with firewall / reverse proxy rules
- review admin logs and REST access metrics
- test backup restore before depending on it in production
