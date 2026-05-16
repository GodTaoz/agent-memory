"""Protocol parity tests for REST and MCP surfaces."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from memory_mcp.protocol.mcp import MCPServer
from memory_mcp.protocol.rest import create_app


def make_memory_dict(memory_id: str, content: str, **overrides) -> dict:
    """Build a complete memory payload for protocol parity tests."""
    memory = {
        "id": memory_id,
        "content": content,
        "tags": [],
        "agent": "",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "version": 1,
        "confidence": "high",
        "source": "user",
        "links": [],
        "metadata": {},
    }
    memory.update(overrides)
    return memory


class TestProtocolParity:
    """Cross-protocol contract tests."""

    def test_rest_and_mcp_create_memory_preserve_confidence(self):
        """REST and MCP should both persist the requested confidence level."""
        rest_engine = MagicMock()
        rest_engine.generate_id.return_value = "mem_rest"
        rest_engine.save.return_value = True

        rest_app = create_app(rest_engine)
        rest_client = TestClient(rest_app)

        rest_response = rest_client.post(
            "/api/v1/memories",
            json={
                "content": "Remember this carefully",
                "tags": ["important"],
                "agent": "rest-agent",
                "confidence": "low",
            },
        )

        assert rest_response.status_code == 201
        assert rest_response.json()["confidence"] == "low"
        assert rest_engine.save.call_args.args[0].confidence.value == "low"

        mcp_engine = MagicMock()
        mcp_engine.generate_id.return_value = "mem_mcp"
        mcp_engine.save.return_value = True

        mcp_server = MCPServer(mcp_engine)
        mcp_result = mcp_server.handle_tool_call(
            "memory.save",
            {
                "content": "Remember this carefully",
                "tags": ["important"],
                "agent": "mcp-agent",
                "confidence": "low",
            },
        )

        assert mcp_result["success"] is True
        assert mcp_result["memory"]["confidence"] == "low"
        assert mcp_engine.save.call_args.args[0].confidence.value == "low"

    def test_rest_and_mcp_update_memory_support_confidence_and_metadata(self):
        """REST and MCP should forward update fields supported by the engine."""
        rest_engine = MagicMock()
        rest_engine.update.return_value = MagicMock(
            to_dict=lambda: {
                "id": "mem_rest",
                "content": "Updated content",
                "tags": ["updated"],
                "agent": "rest-agent",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-02T00:00:00+00:00",
                "version": 2,
                "confidence": "medium",
                "source": "user",
                "links": [],
                "metadata": {"topic": "project"},
            }
        )

        rest_app = create_app(rest_engine)
        rest_client = TestClient(rest_app)
        rest_response = rest_client.put(
            "/api/v1/memories/mem_rest",
            json={"confidence": "medium", "metadata": {"topic": "project"}},
        )

        assert rest_response.status_code == 200
        assert rest_response.json()["confidence"] == "medium"
        assert rest_response.json()["metadata"] == {"topic": "project"}
        assert rest_engine.update.call_args.args == (
            "mem_rest",
            {"confidence": "medium", "metadata": {"topic": "project"}},
        )

        mcp_engine = MagicMock()
        mcp_engine.update.return_value = MagicMock(
            to_dict=lambda: {
                "id": "mem_mcp",
                "content": "Updated content",
                "tags": ["updated"],
                "agent": "mcp-agent",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-02T00:00:00+00:00",
                "version": 2,
                "confidence": "medium",
                "source": "user",
                "links": [],
                "metadata": {"topic": "project"},
            }
        )

        mcp_server = MCPServer(mcp_engine)
        mcp_result = mcp_server.handle_tool_call(
            "memory.update",
            {"id": "mem_mcp", "confidence": "medium", "metadata": {"topic": "project"}},
        )

        assert mcp_result["memory"]["confidence"] == "medium"
        assert mcp_result["memory"]["metadata"] == {"topic": "project"}
        assert mcp_engine.update.call_args.args == (
            "mem_mcp",
            {"confidence": "medium", "metadata": {"topic": "project"}},
        )

    def test_rest_and_mcp_get_and_delete_share_core_success_semantics(self):
        """REST and MCP should expose the same memory payload and delete success semantics."""
        memory_payload = make_memory_dict(
            "mem_123",
            "Shared memory",
            tags=["shared"],
            agent="agent-1",
            metadata={"scope": "team"},
        )

        rest_engine = MagicMock()
        rest_engine.get.return_value = MagicMock(to_dict=lambda: memory_payload)
        rest_engine.delete.return_value = True

        rest_app = create_app(rest_engine)
        rest_client = TestClient(rest_app)
        rest_get_response = rest_client.get("/api/v1/memories/mem_123")
        rest_delete_response = rest_client.delete("/api/v1/memories/mem_123")

        assert rest_get_response.status_code == 200
        assert rest_get_response.json() == memory_payload
        assert rest_delete_response.status_code == 200
        assert rest_delete_response.json() == {"success": True}

        mcp_engine = MagicMock()
        mcp_engine.get.return_value = MagicMock(to_dict=lambda: memory_payload)
        mcp_engine.delete.return_value = True

        mcp_server = MCPServer(mcp_engine)
        mcp_get_result = mcp_server.handle_tool_call("memory.get", {"id": "mem_123"})
        mcp_delete_result = mcp_server.handle_tool_call("memory.delete", {"id": "mem_123"})

        assert mcp_get_result["memory"] == memory_payload
        assert mcp_delete_result == {"success": True}

    def test_rest_and_mcp_invalid_confidence_rejected_as_client_error(self):
        """REST and MCP should both reject unsupported confidence values."""
        rest_engine = MagicMock()
        rest_app = create_app(rest_engine)
        rest_client = TestClient(rest_app)

        rest_create_response = rest_client.post(
            "/api/v1/memories",
            json={"content": "Bad confidence", "confidence": "bogus"},
        )
        rest_update_response = rest_client.put(
            "/api/v1/memories/mem_123",
            json={"confidence": "bogus"},
        )

        assert rest_create_response.status_code == 422
        assert rest_update_response.status_code == 422
        rest_engine.save.assert_not_called()
        rest_engine.update.assert_not_called()

        mcp_engine = MagicMock()
        mcp_server = MCPServer(mcp_engine)
        mcp_create_result = mcp_server.handle_tool_call(
            "memory.save",
            {"content": "Bad confidence", "confidence": "bogus"},
        )
        mcp_update_result = mcp_server.handle_tool_call(
            "memory.update",
            {"id": "mem_123", "confidence": "bogus"},
        )

        assert "error" in mcp_create_result
        assert "valid Confidence" in mcp_create_result["error"]
        assert "error" in mcp_update_result
        assert "valid Confidence" in mcp_update_result["error"]

    def test_rest_list_endpoint_openapi_matches_documented_envelope(self):
        """REST OpenAPI should publish the same list/search envelope documented for parity."""
        rest_engine = MagicMock()
        rest_app = create_app(rest_engine)
        rest_client = TestClient(rest_app)

        openapi_response = rest_client.get("/openapi.json")

        assert openapi_response.status_code == 200
        schema = openapi_response.json()
        list_schema = schema["paths"]["/api/v1/memories"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]

        assert list_schema["$ref"].endswith("MemoryListResponse")

    def test_rest_and_mcp_list_and_search_include_total_counts(self):
        """REST and MCP list/search responses should both expose total counts."""
        listed_memories = [
            MagicMock(to_dict=lambda: make_memory_dict("1", "Memory 1")),
            MagicMock(to_dict=lambda: make_memory_dict("2", "Memory 2")),
        ]
        searched_memories = [
            MagicMock(to_dict=lambda: make_memory_dict("3", "Search result")),
        ]

        rest_engine = MagicMock()
        rest_engine.list_memories.return_value = listed_memories
        rest_engine.search.return_value = searched_memories

        rest_app = create_app(rest_engine)
        rest_client = TestClient(rest_app)

        rest_list_response = rest_client.get("/api/v1/memories")
        rest_search_response = rest_client.get("/api/v1/memories?q=test")

        assert rest_list_response.status_code == 200
        assert rest_list_response.json()["total"] == 2
        assert rest_search_response.status_code == 200
        assert rest_search_response.json()["total"] == 1

        mcp_engine = MagicMock()
        mcp_engine.list_memories.return_value = listed_memories
        mcp_engine.search.return_value = searched_memories

        mcp_server = MCPServer(mcp_engine)
        mcp_list_result = mcp_server.handle_tool_call("memory.list", {"limit": 10})
        mcp_search_result = mcp_server.handle_tool_call("memory.search", {"query": "test"})

        assert mcp_list_result["total"] == 2
        assert mcp_search_result["total"] == 1

    def test_rest_and_mcp_missing_resource_errors_are_equivalent(self):
        """REST and MCP should report missing resources with equivalent semantics."""
        rest_engine = MagicMock()
        rest_engine.get.return_value = None
        rest_engine.update.return_value = None
        rest_engine.delete.return_value = False

        rest_app = create_app(rest_engine)
        rest_client = TestClient(rest_app)

        rest_get_response = rest_client.get("/api/v1/memories/missing")
        rest_update_response = rest_client.put(
            "/api/v1/memories/missing",
            json={"content": "Updated content"},
        )
        rest_delete_response = rest_client.delete("/api/v1/memories/missing")

        assert rest_get_response.status_code == 404
        assert rest_get_response.json()["detail"] == "Memory not found"
        assert rest_update_response.status_code == 404
        assert rest_update_response.json()["detail"] == "Memory not found"
        assert rest_delete_response.status_code == 404
        assert rest_delete_response.json()["detail"] == "Memory not found"

        mcp_engine = MagicMock()
        mcp_engine.get.return_value = None
        mcp_engine.update.return_value = None
        mcp_engine.delete.return_value = False

        mcp_server = MCPServer(mcp_engine)
        mcp_get_result = mcp_server.handle_tool_call("memory.get", {"id": "missing"})
        mcp_update_result = mcp_server.handle_tool_call(
            "memory.update",
            {"id": "missing", "content": "Updated content"},
        )
        mcp_delete_result = mcp_server.handle_tool_call("memory.delete", {"id": "missing"})

        assert mcp_get_result == {"error": "Memory not found"}
        assert mcp_update_result == {"error": "Memory not found"}
        assert mcp_delete_result == {"error": "Memory not found"}

    def test_rest_and_mcp_health_and_stats_shapes_match(self):
        """REST and MCP health/stats responses should expose the same core fields."""
        rest_engine = MagicMock()
        rest_engine.count.return_value = 7

        rest_app = create_app(rest_engine)
        rest_client = TestClient(rest_app)

        rest_health_response = rest_client.get("/api/v1/health")
        rest_stats_response = rest_client.get("/api/v1/stats")

        assert rest_health_response.status_code == 200
        assert rest_health_response.json() == {"status": "healthy", "total_memories": 7}
        assert rest_stats_response.status_code == 200
        assert rest_stats_response.json() == {"total_memories": 7}

        mcp_engine = MagicMock()
        mcp_engine.count.return_value = 7

        mcp_server = MCPServer(mcp_engine)
        mcp_health_result = mcp_server.handle_tool_call("memory.health", {})
        mcp_stats_result = mcp_server.handle_tool_call("memory.stats", {})

        assert mcp_health_result == {"status": "healthy", "total_memories": 7}
        assert mcp_stats_result == {"total_memories": 7}
