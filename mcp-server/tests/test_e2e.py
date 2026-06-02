"""Integration tests — require a running MCP server (python -m src.server)."""
import json
import urllib.error
import urllib.request

import pytest

_TOKEN = "local-dev-token"


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


def _parse_sse(raw: str) -> dict | None:
    for line in raw.splitlines():
        if line.startswith("data:"):
            return json.loads(line[len("data:"):].strip())
    return None


def _tool_call(server_url: str, session_id: str, name: str, arguments: dict):
    status, _, body = _post(
        server_url,
        {"jsonrpc": "2.0", "method": "tools/call",
         "params": {"name": name, "arguments": arguments}, "id": 1},
        {"mcp-session-id": session_id},
    )
    return status, _parse_sse(body) if status == 200 else None


def _text(parsed: dict | None) -> str:
    content = (parsed or {}).get("result", {}).get("content", [])
    return content[0].get("text", "") if content else ""


def _rows(parsed: dict | None) -> list:
    rows = []
    for item in (parsed or {}).get("result", {}).get("content", []):
        try:
            rows.append(json.loads(item.get("text", "")))
        except json.JSONDecodeError:
            if item.get("text"):
                rows.append(item["text"])
    return rows


def _is_error(parsed: dict | None) -> bool:
    return bool((parsed or {}).get("result", {}).get("isError", False))


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def test_no_token_returns_403(server_url):
    payload = {"jsonrpc": "2.0", "method": "initialize",
               "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                          "clientInfo": {"name": "t", "version": "1"}}, "id": 0}
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    req = urllib.request.Request(
        server_url, json.dumps(payload).encode(), headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    assert status == 403


def test_wrong_token_returns_403(server_url):
    payload = {"jsonrpc": "2.0", "method": "initialize",
               "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                          "clientInfo": {"name": "t", "version": "1"}}, "id": 0}
    status, _, _ = _post(server_url, payload, token="wrong-token")
    assert status == 403


def test_health_endpoint_no_auth(server_url):
    health_url = server_url.rsplit("/mcp", 1)[0] + "/health"
    resp = urllib.request.urlopen(health_url, timeout=5)
    assert resp.status == 200
    body = json.loads(resp.read().decode())
    assert body["status"] == "healthy"
    assert "service" in body


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def test_list_tables(server_url, mcp_session_id):
    status, parsed = _tool_call(server_url, mcp_session_id, "list_tables",
                                {"schema_name": "analytics"})
    assert status == 200
    names = [r.get("table_name") for r in _rows(parsed) if isinstance(r, dict)]
    assert "sample_orders" in names


def test_preview_data(server_url, mcp_session_id):
    status, parsed = _tool_call(server_url, mcp_session_id, "preview_data",
                                {"query": "SELECT * FROM analytics.sample_orders"})
    assert status == 200
    rows = _rows(parsed)
    assert len(rows) == 3
    assert len(rows) <= 50


def test_get_table_ddl(server_url, mcp_session_id):
    status, parsed = _tool_call(server_url, mcp_session_id, "get_table_ddl",
                                {"schema": "analytics", "table": "sample_orders"})
    assert status == 200
    assert "order_id" in _text(parsed)


def test_explain_query(server_url, mcp_session_id):
    status, parsed = _tool_call(server_url, mcp_session_id, "explain_query",
                                {"query": "SELECT * FROM analytics.sample_orders"})
    assert status == 200
    assert _text(parsed)


# ---------------------------------------------------------------------------
# Security gatekeeper (via HTTP)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tool,query", [
    ("preview_data", "DROP TABLE analytics.sample_orders"),
    ("preview_data", "INSERT INTO analytics.sample_orders VALUES (99,1,1)"),
    ("explain_query", "DELETE FROM analytics.sample_orders"),
])
def test_gatekeeper_blocks_dml(server_url, mcp_session_id, tool, query):
    status, parsed = _tool_call(server_url, mcp_session_id, tool, {"query": query})
    assert status == 200
    assert _is_error(parsed)
