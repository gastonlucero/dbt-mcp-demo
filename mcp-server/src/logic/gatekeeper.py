import logging

import sqlglot
from sqlglot import expressions as exp

logger = logging.getLogger(__name__)

# In sqlglot 30+, EXPLAIN and SHOW fall back to exp.Command.
# The command name is inspected explicitly to distinguish safe commands.
_SAFE_COMMANDS = frozenset({"EXPLAIN", "SHOW"})

# Dangerous DML/DDL nodes that must be blocked at any level of the AST
_FORBIDDEN_NODES = frozenset({
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.Merge,
    exp.Grant,
    exp.Revoke,
})


class McpSecurityError(Exception):
    """Raised when a SQL query violates the read-only security policy."""

    pass


def _scan_for_forbidden_nodes(ast) -> None:
    """Prevents attacks like SELECT * FROM (DELETE FROM users RETURNING *) AS x."""
    for node in ast.walk():
        if type(node) in _FORBIDDEN_NODES:
            logger.warning(
                "Blocked forbidden node '%s' in query. Node: %s",
                type(node).__name__,
                str(node)[:200],
            )
            raise McpSecurityError(
                f"Forbidden: query contains {type(node).__name__} operation. "
                f"Only SELECT, EXPLAIN and SHOW are permitted."
            )


def validate_schema(query: str, allowed_schema: str) -> None:
    """Raises McpSecurityError if any table in the query is outside allowed_schema."""
    ast = sqlglot.parse_one(query, read="postgres")
    for table in ast.find_all(exp.Table):
        schema = table.db
        if not schema:
            raise McpSecurityError(
                f"Table '{table.name}' must be schema-qualified "
                f"(e.g. {allowed_schema}.{table.name})."
            )
        if schema.lower() != allowed_schema.lower():
            raise McpSecurityError(
                f"Access denied: schema '{schema}' is not allowed. "
                f"Only '{allowed_schema}' is permitted."
            )


def validate_sql(query: str, limit_rows: bool = False) -> str:
    """Validate SQL against the read-only whitelist. Raises McpSecurityError on DML/DDL."""
    ast = sqlglot.parse_one(query, read="postgres")

    # Step 1: Validate root node type
    if isinstance(ast, exp.Select):
        logger.info("Query validated — SELECT")

    elif isinstance(ast, exp.Command):
        cmd = (ast.this or "").upper()
        if cmd not in _SAFE_COMMANDS:
            logger.warning("Blocked Command '%s'. Query (truncated): %s", cmd, query[:200])
            raise McpSecurityError(
                f"Forbidden: command '{cmd}' is not in the safe whitelist "
                f"({', '.join(sorted(_SAFE_COMMANDS))})."
            )
        logger.info("Query validated — Command: %s", cmd)

    else:
        logger.warning(
            "Blocked query — root node '%s'. Query (truncated): %s",
            type(ast).__name__,
            query[:200],
        )
        raise McpSecurityError(
            f"Forbidden: only SELECT, EXPLAIN and SHOW are permitted. "
            f"Got: {type(ast).__name__}"
        )

    # Step 2: Scan entire AST for forbidden DML/DDL operations at any depth
    _scan_for_forbidden_nodes(ast)

    if limit_rows:
        wrapped = f"SELECT * FROM ({query}) AS mcp_limit_wrapper LIMIT 50"
        logger.info("Query wrapped with LIMIT 50")
        return wrapped

    return query



