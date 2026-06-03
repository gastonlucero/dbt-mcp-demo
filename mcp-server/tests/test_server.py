"""Basic smoke tests for the MCP server and its four tools.

These hit a running stack over HTTP. If the server isn't up, the whole module is
skipped — so the fast unit tests (test_gatekeeper.py) still run on their own.

Run the stack first:  docker compose -f docker/docker-compose.yml up -d --build
"""
import json
import os
import urllib.error
import urllib.request

import pytest

BASE = os.getenv("MCP_BASE_URL", "http://localhost:9001")
TOKEN = os.getenv("AUTH_TOKEN", "test-token")


def _server_up() -> bool:
    try:
        urllib.request.urlopen(f"{BASE}/health", timeout=2)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _server_up(), reason="MCP server not running")


def _call(tool: str, arguments: dict, token: str = TOKEN):
    """POST a tools/call to /mcp. Returns (http_status, parsed_text_or_None)."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    req = urllib.request.Request(
        f"{BASE}/mcp",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, _extract_text(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, None


def _extract_text(body: str):
    """The response is JSON (optionally SSE-wrapped). Pull result.content[0].text."""
    for line in body.splitlines() or [body]:
        line = line.strip()
        if line.startswith("data:"):
            line = line[len("data:"):].strip()
        if line.startswith("{"):
            return json.loads(line)["result"]["content"][0]["text"]
    return None


# --- server ---------------------------------------------------------------

def test_health_endpoint():
    with urllib.request.urlopen(f"{BASE}/health", timeout=5) as resp:
        assert resp.status == 200


def test_missing_token_is_rejected():
    status, _ = _call("list_tables", {"schema_name": "public"}, token="")
    assert status in (401, 403)


# --- the four tools -------------------------------------------------------

def test_list_tables():
    status, text = _call("list_tables", {"schema_name": "public"})
    assert status == 200
    assert "fct_fires__by_country_municipality" in text


def test_get_table_ddl():
    status, text = _call("get_table_ddl", {"schema": "raw_data", "table": "monthly_fires"})
    assert status == 200
    assert "pais" in text


def test_preview_data():
    status, text = _call("preview_data", {"query": "SELECT * FROM raw_data.monthly_fires"})
    assert status == 200
    assert text and text.strip().startswith("[")  # JSON array of rows


def test_explain_query():
    status, text = _call(
        "explain_query",
        {"query": "SELECT pais, count(*) FROM raw_data.monthly_fires GROUP BY pais"},
    )
    assert status == 200
    assert "Aggregate" in text or "Scan" in text


# --- security boundary ----------------------------------------------------

def test_dml_is_blocked():
    status, text = _call("preview_data", {"query": "DELETE FROM raw_data.monthly_fires"})
    # Either an HTTP error or a tool error message — never a successful delete.
    assert status != 200 or (text and "Forbidden" in text)
