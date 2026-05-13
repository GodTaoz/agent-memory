# Development Guide

This guide documents the verified local development flow for `agent-memory`.

## Prerequisites

- Python 3.10+
- A reachable Redis instance
  - default host: `127.0.0.1`
  - default port: `6379`
- Git

## Quick setup

```bash
git clone https://github.com/GodTaoz/agent-memory.git
cd agent-memory

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[all]'

cp config/config.example.yaml config/config.yaml
```

## Verification commands

Run the full test suite:

```bash
pytest -q
```

Recommended quality checks before opening a PR:

```bash
black --check src tests
flake8 src tests
mypy src
```

## Running the service locally

Start the API/admin server directly with uvicorn:

```bash
uvicorn memory_mcp.main:create_app --factory --host 0.0.0.0 --port 5678
```

Or use the installed console script:

```bash
memory-mcp
```

Once the server is running, verify the health endpoint:

```bash
curl http://127.0.0.1:5678/api/v1/health
```

Expected response shape:

```json
{"status":"healthy","total_memories":0}
```

## Configuration files

Start from the example files:

- `config/config.example.yaml`
- `config/permissions.example.yaml`

Common local-development settings:

- Redis host/port live in `config/config.yaml`
- managed admin auth state is written under the repository-local `data/`
- admin logs default to `data/admin_logs.db` relative to the current working directory unless `ADMIN_LOG_DB_PATH` is set
- `config/permissions.example.yaml` is an optional reference file for planned ACL/isolation work; the current FastAPI startup path does not load `config/permissions.yaml`

## Troubleshooting

### `ModuleNotFoundError: memory_mcp`

Install the project into your virtualenv before running tests or launching the app:

```bash
pip install -e '.[all]'
```

### Redis connection failure on startup

The application connects to Redis during app creation. If startup fails:

1. ensure Redis is running
2. confirm `config/config.yaml` or environment variables point to the correct host/port
3. verify the password/db settings if your Redis instance is protected
4. if needed, export overrides before startup, for example:

```bash
export REDIS_HOST=192.168.10.10
export REDIS_PASSWORD='your-redis-password'
uvicorn memory_mcp.main:create_app --factory --host 0.0.0.0 --port 5678
```

### Admin files appear under `data/`

This is expected. By default the admin password state and managed API key state are persisted under the repository-local `data/` directory. Admin logs default to `data/admin_logs.db` relative to the process working directory unless `ADMIN_LOG_DB_PATH` is set.
