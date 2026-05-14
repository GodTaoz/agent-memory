# Permissions and Isolation Model

This document defines the current ACL model for `agent-memory` and the intended default isolation semantics for v0.1.

## Goals

The permission model is designed to make multi-agent memory behavior predictable:

- each agent owns a private namespace by default
- cross-agent access is denied unless explicitly configured
- shared spaces are opt-in
- admin agents can bypass normal namespace limits

## Core concepts

### Agent

An `agent` is the caller identity used by the ACL layer.

Examples:

- `hermes`
- `codex`
- `claude`

In the current ACL implementation, the `agent_id` is matched against the configured `agents` map.

### Namespace

A namespace is the resource prefix an agent may access.

Examples:

- `hermes:*`
- `codex:*`
- `${agent_id}:*`

A memory resource such as `hermes:memory:123` belongs to the `hermes` namespace.

### Shared namespace

Shared memory lives in one of the configured shared namespace prefixes.

Current behavior:

- top-level config key: `shared_namespaces`
- default value when omitted: `["shared"]`
- resources matching `<namespace>:` are treated as shared resources for `shared_read`

Examples:

- `shared:memory:123`
- `team:memory:456` when `shared_namespaces: ["shared", "team"]`

## Default rules

### 1. Private memory is allowed inside an agent's namespace

If an agent has:

- a matching `namespace`
- the requested operation in `operations`

then access is allowed.

Example:

- agent: `codex`
- namespace: `codex:*`
- resource: `codex:memory:123`
- operation: `read`

Result: allowed.

### 2. Cross-agent access is denied by default

If a resource does not match the agent's private namespace, access is denied unless one of the explicit exceptions below applies.

Example:

- agent: `codex`
- namespace: `codex:*`
- resource: `hermes:memory:123`

Result: denied.

### 3. Shared reads are opt-in

If an agent has `shared_read: true`, it may read resources under any configured shared namespace.

Example:

```yaml
shared_namespaces: ["shared", "team"]

agents:
  codex:
    permissions:
      namespace: "codex:*"
      operations: ["read", "write"]
      shared_read: true
```

Allowed:

- `read shared:memory:123`
- `read team:memory:456`

Denied:

- `write shared:memory:123`
- `write team:memory:456`
- `read hermes:memory:123`

### 4. Admin overrides namespace restrictions

If an agent has `admin: true`, ACL grants all operations on all resources.

This is intended for trusted operators and maintenance paths.

## Configuration shape

Example ACL config:

```yaml
shared_namespaces: ["shared", "team"]

agents:
  hermes:
    name: "Hermes Agent"
    permissions:
      namespace: "hermes:*"
      operations: ["read", "write", "delete"]
      admin: true

  codex:
    name: "Codex CLI"
    permissions:
      namespace: "codex:*"
      operations: ["read", "write"]
      shared_read: true

  default:
    permissions:
      namespace: "${agent_id}:*"
      operations: ["read", "write"]
```

## Current implementation notes

The ACL foundation currently lives in:

- `src/memory_mcp/auth/acl.py`

Verified behaviors covered by tests:

- private namespace access
- operation allow/deny checks
- default-agent fallback
- admin override
- shared-read access for configured shared namespaces

## Known limitation

The repository contains the ACL foundation and configuration examples, but the current FastAPI startup path still does not fully wire `config/permissions.yaml` into runtime enforcement for every protocol surface.

So this document describes the intended contract and the verified ACL component behavior, while broader end-to-end enforcement remains ongoing roadmap work.
