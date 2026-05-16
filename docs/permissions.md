# Permissions and multi-agent isolation

This document defines the current v0.1 isolation model for `agent-memory`.

## Terms

- **agent**: the logical owner/namespace of a memory entry, stored in the memory object's `agent` field.
- **managed REST API key**: a key created through the admin panel/API and persisted in `data/api_keys.json`.
- **bootstrap API key**: a key supplied through the `API_KEYS` environment variable.
- **admin request**: a request authenticated with an admin-permission key.

## Canonical model in v0.1

The current runtime model is:

- memories are **private to one agent by default**
- managed REST API keys are **tenant-bound identities**
- cross-agent access is **denied by default** for non-admin REST keys
- admin keys can access all memories
- the reserved `shared` agent namespace is **readable by managed non-admin REST keys by default**, unless an active ACL disables `shared_read` for that identity
- only admin keys can create, update, or delete `shared` memories
- authenticated MCP transport/auth remains unimplemented, so this runtime rule currently applies to REST only

## How managed REST API keys map to agent identity

Each managed API key has:

- `name`
- `permissions` (`read`, `read_write`, or `admin`)
- `agent_id`

If `agent_id` is omitted when creating a managed key, it defaults to the key `name`.

The reserved shared namespace also reserves the corresponding identity:

- non-admin managed keys may **not** resolve to `agent_id = "shared"`
- admin keys may still use that identity when they intentionally manage shared memories

Example:

- create key: `{ "name": "alice", "permissions": "read_write" }`
- resolved identity: `agent_id = "alice"`

This makes the default behavior private-per-agent without requiring a second field in the common case.

## REST enforcement rules

### Read-only vs write-capable

- `read`: may perform read-only REST requests
- `read_write`: may perform memory CRUD requests
- `admin`: unrestricted REST access

## Memory ownership rules for managed non-admin REST keys

For a managed non-admin key bound to `agent_id = X`:

### Create

- if the request omits `agent`, the server stores the memory with `agent = X`
- if the request sets `agent = X`, the request succeeds
- if the request sets `agent` to any other value, the request is rejected with `403`

### List / search

- default results include:
  - private memories with `agent = X`
  - shared memories with `agent = "shared"` when the active ACL allows `shared_read`
- requesting another private agent namespace through the `agent` filter is rejected with `403`
- requesting `agent=shared` is allowed only when the active ACL allows shared reads, and returns shared memories only

### Get / update / delete

- `get` succeeds when the target memory has `agent = X` or `agent = "shared"`
- `update` and `delete` succeed only when the target memory has `agent = X`
- non-admin keys cannot modify shared memories; those requests return `403`
- accessing another agent's private memory returns `403`

## Admin behavior

Admin keys are not tenant-scoped:

- admin can create memories for any `agent`
- admin can list/search across all agents
- admin can read/update/delete any memory

Bootstrap `API_KEYS` are treated as admin-permission keys in the current runtime.

## Shared memory status

The runtime now reserves `agent = "shared"` as a simple shared-read namespace for REST.

Current status:

- private per-agent access: implemented for managed REST keys
- admin override: implemented
- shared read namespace (`agent = "shared"`): implemented for REST
- shared writes by non-admin keys: denied
- tenant-aware MCP transport/auth: not implemented yet
- `/api/v1/health` and `/api/v1/stats` still expose global operational counts; they are not tenant-scoped endpoints yet

## ACL module status

The repository contains `src/memory_mcp/auth/acl.py`, and the current FastAPI runtime now loads `config/permissions.yaml` when present.

Today, the authoritative runtime enforcement for REST is:

1. REST API key permission class (`read` / `read_write` / `admin`)
2. managed-key `agent_id` ownership checks in the REST layer
3. optional ACL checks loaded from `config/permissions.yaml` for managed REST keys

The current runtime wiring intentionally remains REST-only:

- managed REST keys use ACL checks for read/write/delete namespace decisions when `config/permissions.yaml` is present
- malformed ACL config shape fails startup instead of silently disabling enforcement
- bootstrap `API_KEYS` remain admin-like compatibility keys; they are not tenant-scoped by the ACL file
- authenticated MCP transport/auth still does not enforce this ACL yet

## Examples

### Private per-agent key

Create a managed key in the admin API:

```json
{
  "name": "research-bot",
  "permissions": "read_write"
}
```

Resolved runtime identity:

```json
{
  "agent_id": "research-bot"
}
```

Then a create request like:

```json
{
  "content": "Track paper ideas"
}
```

is stored as:

```json
{
  "agent": "research-bot"
}
```

### Explicit tenant binding

```json
{
  "name": "worker-key",
  "permissions": "read_write",
  "agent_id": "planner"
}
```

This key acts as the `planner` agent, regardless of the display name `worker-key`.

### Shared read namespace

Admin can publish a shared memory:

```json
{
  "content": "Team runbook",
  "agent": "shared"
}
```

Managed non-admin keys can:

- see this memory in the default `GET /api/v1/memories` listing alongside their private memories when the active ACL allows `shared_read`
- request `GET /api/v1/memories?agent=shared` to see only shared memories when the active ACL allows shared reads
- fetch the memory directly by ID when the active ACL allows shared reads

Managed non-admin keys cannot:

- create a memory with `agent = "shared"`
- update or delete a shared memory

## Known limitations

- REST list pagination still uses the current response-size `total` contract from `docs/protocol-parity.md`
- tenant isolation is enforced in REST, not yet in an authenticated MCP transport
- only the reserved REST `shared` namespace is implemented; richer shared grants and explicit cross-agent ACLs remain future work
- the admin agent-management view now surfaces managed API-key identities and ACL-only agents, but richer per-agent analytics and non-REST identity sources remain future work
