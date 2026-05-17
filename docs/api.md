# REST API Guide

This document describes the verified REST surface exposed by `agent-memory` at `/api/v1/*`.

## Base URL

Default local base URL:

```text
http://localhost:5678/api/v1
```

## Authentication

Memory endpoints accept any of these auth styles:

- `Authorization: Bearer <api_key>`
- `X-API-Key: <api_key>`
- `?api_key=<api_key>`

Operational endpoints like `/health` are intentionally service-wide and may be used without a managed key depending on deployment mode.

## Endpoints

### Health

```bash
curl http://localhost:5678/api/v1/health
```

Example response:

```json
{
  "status": "healthy",
  "total_memories": 3
}
```

### Stats

`/stats` follows normal API-key enforcement when the service is running in managed-key mode.

```bash
curl -H 'X-API-Key: your-api-key' \
  http://localhost:5678/api/v1/stats
```

### Create memory

```bash
curl -X POST http://localhost:5678/api/v1/memories \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "content": "User prefers concise code.",
    "tags": ["preference", "coding"],
    "agent": "hermes",
    "confidence": "high"
  }'
```

### Get memory

```bash
curl -H 'X-API-Key: your-api-key' \
  http://localhost:5678/api/v1/memories/<memory_id>
```

### Update memory

```bash
curl -X PUT http://localhost:5678/api/v1/memories/<memory_id> \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "confidence": "medium",
    "metadata": {"topic": "project"}
  }'
```

### Delete memory

```bash
curl -X DELETE \
  -H 'X-API-Key: your-api-key' \
  http://localhost:5678/api/v1/memories/<memory_id>
```

### List memories

```bash
curl -H 'X-API-Key: your-api-key' \
  'http://localhost:5678/api/v1/memories?limit=20&offset=0'
```

Example response envelope:

```json
{
  "memories": [],
  "total": 0
}
```

### Search memories

```bash
curl -H 'X-API-Key: your-api-key' \
  'http://localhost:5678/api/v1/memories?q=concise&agent=hermes&limit=10'
```

## Multi-agent behavior

Managed REST keys are tenant-bound by default:

- non-admin keys act as their configured `agent_id`
- private memories are isolated per agent by default
- the reserved shared namespace can be included for read paths when ACL allows it
- only admin keys may mutate shared memories

See [`docs/permissions.md`](permissions.md) for the full model.

## OpenAPI

When the server is running, the generated schema is available at:

```text
http://localhost:5678/openapi.json
```

This is covered by parity tests to keep the documented list/search envelopes aligned with runtime behavior.
