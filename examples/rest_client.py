"""Minimal REST client example for agent-memory."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

BASE_URL = os.environ.get("AGENT_MEMORY_BASE_URL", "http://127.0.0.1:5678/api/v1")
API_KEY = os.environ.get("AGENT_MEMORY_API_KEY", "")


def request_json(method: str, path: str, payload: dict | None = None) -> dict:
    """Send a JSON request to the REST API and parse the response."""
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        method=method,
        headers={
            "Content-Type": "application/json",
            **({"X-API-Key": API_KEY} if API_KEY else {}),
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"HTTP {exc.code}: {exc.read().decode('utf-8')}") from exc


def main() -> None:
    """Save and search a sample memory."""
    created = request_json(
        "POST",
        "/memories",
        {
            "content": "User prefers concise code.",
            "tags": ["preference", "coding"],
            "agent": "example-client",
            "confidence": "high",
        },
    )
    print("Created memory:")
    print(json.dumps(created, indent=2, ensure_ascii=False))

    search_result = request_json(
        "GET",
        "/memories?q=concise&agent=example-client",
    )
    print("\nSearch result:")
    print(json.dumps(search_result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
