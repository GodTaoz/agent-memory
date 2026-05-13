# agent-memory

> A lightweight, local-first memory service for AI agents with **MCP + REST API**, built-in **admin panel**, and **zero external API cost**.

[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Branch](https://img.shields.io/badge/default%20branch-master-blueviolet.svg)](https://github.com/GodTaoz/agent-memory)

`agent-memory` helps multiple AI agents share durable memory through standard protocols instead of re-embedding state into every conversation.
It is designed to be:

- **Lightweight**: Redis only, no vector DB required for v1
- **Protocol-friendly**: MCP for agent-native integration, REST for universal access
- **Local-first**: deploy on your own machine or NAS
- **Secure by default (baseline)**: API key auth for REST, admin login for the panel
- **Operable**: built-in web admin panel for inspection, API key management, and monitoring

---

## Features

### Core memory service
- MCP + REST dual protocol support
- Redis-backed persistence
- Memory CRUD and list/search APIs
- Multi-level indexing: agent / tag / keyword / time
- Memory evolution hooks for future merge and semantic upgrades
- ACL-oriented multi-agent isolation foundation

### Admin panel
- Single-port deployment on **`5678`**
- Vue 3 + Element Plus frontend
- Light / dark / system theme switching
- Dashboard with live Redis / memory / API key / request stats
- API key management: list / create / delete / usage tracking
- Memory browse / search / edit / delete / export
- Agent activity overview (placeholder UI, backend extension point)
- SQLite-backed admin + REST access statistics
- Admin password login, in-panel password change, failed-login lockout, and default-password warning signal

### Security
- REST API key authentication
- Managed API key permissions:
  - `read` → read-only REST access
  - `read_write` → full memory CRUD over REST
  - `admin` → reserved / bootstrap-compatible full access
- Supported auth methods:
  - `Authorization: Bearer <api_key>`
  - `X-API-Key: <api_key>`
  - `?api_key=<api_key>`
- Separate admin login flow for the management panel
- Recommended production hardening: HTTPS, firewall/IP whitelist, key rotation

---

## Architecture

```text
Browser
  └─ http://host:5678/
       ├─ /admin/api/*        Admin backend (FastAPI)
       ├─ /assets/*           Built Vue frontend assets
       ├─ /api/v1/*           Memory REST API
       └─ /                   Admin panel entry

AI Agents
  ├─ MCP client  ─────────────┐
  └─ REST client ─────────────┤
                              ▼
                    agent-memory service
                      ├─ protocol layer
                      ├─ auth layer
                      ├─ memory engine
                      ├─ index manager
                      ├─ admin module
                      └─ Redis / SQLite
```

---

## Quick start

### Option 1: Docker Compose

```bash
git clone https://github.com/GodTaoz/agent-memory.git
cd agent-memory

cp config/config.example.yaml config/config.yaml
cp config/permissions.example.yaml config/permissions.yaml

# optional: export runtime secrets
export REDIS_PASSWORD='your-redis-password'
export API_KEYS='agent-key-1,agent-key-2'
export ADMIN_PASSWORD_HASH=''
export ADMIN_PASSWORD_SALT=''

docker-compose up -d
```

Then open:

- Admin panel: `http://localhost:5678/`
- Health check: `http://localhost:5678/api/v1/health`

### Option 2: Local development

```bash
git clone https://github.com/GodTaoz/agent-memory.git
cd agent-memory

python3 -m venv venv
source venv/bin/activate
pip install -e ".[all]"

# start backend
uvicorn memory_mcp.main:create_app --factory --host 0.0.0.0 --port 5678
```

If you want to run via console script after installation:

```bash
memory-mcp
```

---

## Admin panel

The admin panel is served from the same port as the API.

- URL: `http://<host>:5678/`
- Default password: `admin123`
- **Important:** change it immediately after the first login

### Current panel scope

- Dashboard / service stats (live Redis + request metrics)
- API key management (create / list / revoke)
- Memory inspection and editing
- Agent overview shell (backend can be extended further)
- Operation logs API and REST access metrics
- Export entry points
- Theme switching: light / dark / follow system

Admin logs are stored in SQLite by default:

- default file: `data/admin_logs.db`
- configurable via `ADMIN_LOG_DB_PATH`

Admin auth / API key persistence defaults:

- admin password state: `data/admin_auth.json`
- managed API keys: `data/api_keys.json`

---

## REST API usage

### Save memory

```bash
curl -X POST http://localhost:5678/api/v1/memories \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "content": "User prefers concise and elegant code.",
    "tags": ["preference", "coding"],
    "agent": "hermes"
  }'
```

### Search memory

```bash
curl 'http://localhost:5678/api/v1/memories?q=concise&agent=hermes&api_key=your-api-key'
```

### Health check

```bash
curl http://localhost:5678/api/v1/health
```

### Main endpoints

- `POST /api/v1/memories`
- `GET /api/v1/memories/{id}`
- `PUT /api/v1/memories/{id}`
- `DELETE /api/v1/memories/{id}`
- `GET /api/v1/memories`
- `GET /api/v1/health`
- `GET /api/v1/stats`

---

## MCP integration

Example stdio client usage:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["-m", "memory_mcp.protocol.mcp"],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        await session.call_tool("memory.save", {
            "content": "User prefers concise and elegant code.",
            "tags": ["preference", "coding"],
        })
```

---

## Configuration

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `SERVER_HOST` | `0.0.0.0` | Bind host |
| `SERVER_PORT` | `5678` | Service port |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | empty | Redis password |
| `REDIS_DB` | `0` | Redis database index |
| `API_KEYS` | empty | Bootstrap REST API keys (optional compatibility path) |
| `ADMIN_PASSWORD_HASH` | empty | Optional hashed admin password |
| `ADMIN_PASSWORD_SALT` | empty | Salt for the hashed admin password |
| `ADMIN_AUTH_CONFIG_PATH` | `data/admin_auth.json` | Persisted admin password state |
| `ADMIN_API_KEYS_PATH` | `data/api_keys.json` | Persisted managed API keys |
| `ADMIN_LOG_DB_PATH` | `data/admin_logs.db` | SQLite path for admin logs and REST access stats |
| `LOG_LEVEL` | `INFO` | Log level |

### Config files

- `config/config.yaml` - server / Redis / search / logging config
- `config/permissions.yaml` - agent permissions / ACL-related config

You can start from:

- `config/config.example.yaml`
- `config/permissions.example.yaml`

---

## Frontend development

The admin frontend lives in `admin-frontend/`.

```bash
cd admin-frontend
npm install
npm run build
```

The built files are published to:

- `src/memory_mcp/admin/static/`

This repository keeps the built static assets in version control so the admin panel can be served directly by the backend in deployments.

---

## Development

### Run tests

```bash
pytest
```

### Suggested checks

```bash
black src tests
flake8 src tests
mypy src
```

### Branch policy

This repository uses **`master`** as the default working branch.

---

## Project structure

```text
agent-memory/
├── admin-frontend/              # Vue 3 admin UI source
├── config/                      # Example and runtime config
├── src/memory_mcp/
│   ├── admin/                   # Admin backend + built static files
│   ├── auth/                    # Auth and ACL modules
│   ├── engine/                  # Memory lifecycle logic
│   ├── protocol/                # MCP / REST interfaces
│   ├── storage/                 # Redis backend and indexes
│   ├── config.py                # Config loader
│   ├── models.py                # Data model
│   └── main.py                  # Runtime entrypoint
├── tests/                       # Test suite
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

## Security notes

Current baseline security includes REST API key auth and admin login, and the admin flow now also includes:

- default-password detection (`requires_password_change` on login)
- persisted admin password state
- managed API key persistence + revocation
- enforced API key permissions (`read` vs `read_write`)
- login / admin mutation / REST access audit logs in SQLite
- failed-login lockout after repeated attempts
- password state file permissions tightened to owner-only (`0600`)
- API key store file permissions tightened to owner-only (`0600`)

For production you should still add:

- HTTPS / TLS
- reverse proxy (Nginx / Caddy) if exposed publicly
- firewall or source IP restrictions
- strong random API keys
- password rotation and audit review

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

This project is licensed under the [MIT License](LICENSE).
