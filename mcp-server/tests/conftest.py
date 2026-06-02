"""Shared fixtures for integration tests (require a running MCP server)."""
import json
import os
import urllib.error
import urllib.request

import pytest

pytest_plugins = ('pytest_asyncio',)

_BASE_URL = os.getenv("BASE_URL", "http://localhost:9001/mcp")
_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")


def _server_is_up() -> bool:
    try:
        urllib.request.urlopen("http://localhost:9001/health", timeout=2)
        return True
    except Exception:
        return False


def _post(url: str, payload: dict, extra_headers: dict = None, token: str = _TOKEN):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if extra_headers:
        headers.update(extra_headers)
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, dict(resp.headers), resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()


@pytest.fixture(scope="session")
def server_url():
    if not _server_is_up():
        pytest.skip("MCP server not running — start with 'python -m src.server'")
    return _BASE_URL


@pytest.fixture(scope="session")
def mcp_session_id(server_url):
    status, headers, _ = _post(server_url, {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pytest-e2e", "version": "1.0"},
        },
        "id": 0,
    })
    assert status == 200, f"MCP initialize failed with HTTP {status}"
    session_id = headers.get("mcp-session-id")
    assert session_id, "No mcp-session-id returned"
    _post(server_url, {"jsonrpc": "2.0", "method": "notifications/initialized"},
          {"mcp-session-id": session_id})
    return session_id
