# REST / MCP protocol parity checklist

This document defines the current v0.1 contract shared by the REST and MCP surfaces.

## Shared memory object fields

When an operation returns a memory object, the memory payload may include:

- `id`
- `content`
- `tags`
- `agent`
- `created_at`
- `updated_at`
- `version`
- `confidence`
- `source`
- `links`
- `metadata`

## Operation checklist

### Save

- REST: `POST /api/v1/memories`
  - success: HTTP `201` with the memory object as the top-level JSON body
- MCP: `memory.save`
  - success: `{ "success": true, "memory": { ... } }`
- Shared semantics:
  - accepts `content`, `tags`, `agent`, `confidence`
  - persists the requested `confidence`

### Get

- REST: `GET /api/v1/memories/{id}`
  - success: HTTP `200` with the memory object as the top-level JSON body
- MCP: `memory.get`
  - success: `{ "memory": { ... } }`
- Shared semantics:
  - returns the same underlying memory fields for the same stored memory

### Update

- REST: `PUT /api/v1/memories/{id}`
  - success: HTTP `200` with the updated memory object as the top-level JSON body
- MCP: `memory.update`
  - success: `{ "memory": { ... } }`
- Shared semantics:
  - supports `content`, `tags`, `confidence`, `metadata`
  - forwards `confidence` and `metadata` updates to the engine

### Delete

- REST: `DELETE /api/v1/memories/{id}`
  - success: `{ "success": true }`
- MCP: `memory.delete`
  - success: `{ "success": true }`

### List

- REST: `GET /api/v1/memories?limit=<n>&offset=<n>`
- MCP: `memory.list`
- Success shape on both surfaces:

```json
{
  "memories": [{ "id": "..." }],
  "total": 1
}
```

### Search

- REST: `GET /api/v1/memories?q=<query>&tags=a,b&agent=name&limit=<n>`
- MCP: `memory.search`
- Success shape on both surfaces:

```json
{
  "memories": [{ "id": "..." }],
  "total": 1
}
```

### Health

- REST: `GET /api/v1/health`
- MCP: `memory.health`
- Success shape on both surfaces:

```json
{
  "status": "healthy",
  "total_memories": 0
}
```

### Stats

- REST: `GET /api/v1/stats`
- MCP: `memory.stats`
- Success shape on both surfaces:

```json
{
  "total_memories": 0
}
```

## Error semantics

Protocol-specific transport details differ, but the semantic outcome should match:

- REST reports client/server errors with HTTP status codes and JSON error bodies.
  - Missing resource: HTTP `404` with `{ "detail": "Memory not found" }`
  - Validation failures: HTTP `422` with FastAPI/Pydantic validation details
- MCP reports tool failures in the returned payload.
  - Missing resource: `{ "error": "Memory not found" }`
  - Invalid tool input: `{ "error": "..." }`

The transport envelope is intentionally different, but a caller should observe the same meaning:

- missing resource -> not found
- invalid request -> validation/input error
- successful read/write -> same underlying memory field semantics

## Pagination and search semantics

Current v0.1 behavior:

- `limit` caps the number of returned items
- `offset` is supported for list operations only
- `total` is the number of items included in the current response payload, not the total number of memories in storage before pagination
- search uses filtered result semantics and returns the same `memories` + `total` envelope shape as list

If global pre-pagination totals are introduced later, the contract must be updated deliberately on both surfaces and covered by parity regression tests.
