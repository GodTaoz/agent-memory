# Hermes Agent integration example

Add the stdio runtime to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  agent_memory:
    command: "/absolute/path/to/your/venv/bin/memory-mcp-stdio"
    timeout: 120
    connect_timeout: 30
    env:
      REDIS_HOST: "127.0.0.1"
      REDIS_PORT: "6379"
      REDIS_PASSWORD: ""
```

Then restart Hermes Agent. The discovered tools will be prefixed with the server name, for example:

- `mcp_agent_memory_memory_save`
- `mcp_agent_memory_memory_search`
- `mcp_agent_memory_memory_get`

If you prefer REST instead of MCP inside Hermes workflows, point Hermes-side automation at the same `agent-memory` service over `http://127.0.0.1:5678/api/v1`.
