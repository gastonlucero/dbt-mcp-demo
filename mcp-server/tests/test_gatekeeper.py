"""Unit tests for the SQL gatekeeper."""
import pytest

from src.logic.gatekeeper import McpSecurityError, validate_sql


def test_valid_select():
    result = validate_sql("SELECT id, name FROM analytics.orders")
    assert "SELECT" in result.upper()


def test_valid_explain():
    result = validate_sql("EXPLAIN SELECT id FROM analytics.orders")
    assert result is not None


def test_select_with_limit_rows_wraps_query():
    result = validate_sql("SELECT * FROM analytics.orders", limit_rows=True)
    assert "LIMIT 50" in result


@pytest.mark.parametrize("sql", [
    "DROP TABLE analytics.orders",
    "INSERT INTO analytics.orders VALUES (1, 2, 100.00)",
    "UPDATE analytics.orders SET amount = 0 WHERE customer_id = 1",
    "DELETE FROM analytics.orders WHERE customer_id = 1",
    "CREATE TABLE analytics.new_table (id INT)",
    "ALTER TABLE analytics.orders ADD COLUMN x INT",
])
def test_forbidden_statements_raise(sql):
    with pytest.raises(McpSecurityError):
        validate_sql(sql)


def test_merge_raises():
    with pytest.raises(McpSecurityError):
        validate_sql("""
            MERGE INTO analytics.orders t
            USING analytics.new_orders s ON t.order_id = s.order_id
            WHEN MATCHED THEN UPDATE SET amount = s.amount
        """)


def test_dml_hidden_in_subquery_raises():
    """DML nested inside a SELECT subquery must still be caught."""
    with pytest.raises(McpSecurityError):
        validate_sql("SELECT * FROM (DELETE FROM analytics.orders RETURNING *) AS x")
