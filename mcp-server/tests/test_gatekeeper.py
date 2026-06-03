"""Basic read-only enforcement for the SQL gatekeeper.

Pure unit tests — no database or running server required. They cover the core
security promise of the MCP tools: read-only queries pass, everything else is blocked.
"""
import pytest

from src.logic.gatekeeper import McpSecurityError, validate_sql


def test_allows_select():
    query = "SELECT pais, count(*) FROM raw_data.monthly_fires GROUP BY pais"
    assert validate_sql(query) == query


def test_injects_limit_when_requested():
    wrapped = validate_sql("SELECT * FROM raw_data.monthly_fires", limit_rows=True)
    assert "LIMIT 50" in wrapped


@pytest.mark.parametrize(
    "query",
    [
        "DELETE FROM raw_data.monthly_fires",
        "DROP TABLE raw_data.monthly_fires",
        "INSERT INTO raw_data.monthly_fires (id) VALUES ('x')",
        "UPDATE raw_data.monthly_fires SET pais = 'X'",
    ],
)
def test_blocks_dml_and_ddl(query):
    with pytest.raises(McpSecurityError):
        validate_sql(query)


def test_blocks_union():
    with pytest.raises(McpSecurityError):
        validate_sql("SELECT 1 UNION SELECT 2")
