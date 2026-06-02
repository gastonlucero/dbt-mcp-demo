import json
import logging
import re
from datetime import date, datetime
from decimal import Decimal

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.auth.middleware import BearerTokenMiddleware
from src.config import settings
from src.logic.database import get_cursor
from src.logic.gatekeeper import McpSecurityError, validate_schema, validate_sql

# Allowlist pattern for SQL identifiers: letters, digits, underscores, dollar sign.
# Prevents SQL injection in statements that do not support parameterized queries.
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def _validate_identifier(value: str, label: str) -> str:
    """Raises McpSecurityError if value contains characters that could allow SQL injection."""
    if not _IDENTIFIER_RE.match(value):
        raise McpSecurityError(
            f"Invalid {label} '{value}': identifiers must match "
            r"^[A-Za-z_][A-Za-z0-9_$]*$ to prevent SQL injection."
        )
    return value

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("MCP Server started — DB:%s:%d User:%s DEV_MODE:%s Schema:%s",
            settings.db_host, settings.db_port, settings.db_user,
            settings.dev_mode, settings.allowed_schema or "any")


def serialize_for_json(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not JSON serializable")


def _check_schema_access(schema: str, label: str = "schema") -> str:
    """Validate identifier and check allowed_schema. Returns safe schema name."""
    safe_schema = _validate_identifier(schema, label)
    if settings.allowed_schema and safe_schema != settings.allowed_schema:
        raise McpSecurityError(
            f"Access denied: {label} '{safe_schema}' is not allowed. "
            f"Only '{settings.allowed_schema}' is permitted."
        )
    return safe_schema


def _cursor_to_dicts(cursor):
    """Convert cursor results to list of dicts."""
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _error_response(msg: str, is_error: bool = True) -> CallToolResult:
    """Build error response."""
    return CallToolResult(
        content=[TextContent(type="text", text=msg)],
        isError=is_error,
    )


# stateless_http=True: every request gets its own Protocol instance, which
# prevents the "Already connected to a transport" error the IDE raises when
# it reconnects (e.g. after a restart) while a previous session is still
# lingering. Correct mode for a stateless, read-only toolbox server.
mcp = FastMCP("dbt-mcp-tools", stateless_http=True, json_response=True)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_tables(schema_name: str) -> CallToolResult:
    """Fetch all table names and types for a given schema via information_schema."""
    try:
        _check_schema_access(schema_name, "schema")
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT table_name, table_type "
                "FROM information_schema.tables "
                "WHERE table_schema = %s "
                "ORDER BY table_name",
                (schema_name,),
            )
            result = _cursor_to_dicts(cursor)
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2, default=serialize_for_json))]
            )
    except McpSecurityError as e:
        logger.warning("list_tables blocked: %s", str(e))
        return _error_response(f"Security Error: {str(e)}")
    except Exception as e:
        logger.error("list_tables failed: %s", str(e), exc_info=True)
        return _error_response(f"Error: {str(e)}\nType: {type(e).__name__}")


@mcp.tool()
def get_table_ddl(schema: str, table: str) -> CallToolResult:
    """Retrieve the physical schema of a table via information_schema.columns."""
    try:
        safe_schema = _check_schema_access(schema, "schema")
        safe_table = _validate_identifier(table, "table")
        with get_cursor() as cursor:
            cursor.execute(
                "SELECT column_name, data_type, character_maximum_length, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s "
                "ORDER BY ordinal_position",
                (safe_schema, safe_table),
            )
            rows = _cursor_to_dicts(cursor)
            result = "\n".join(str(row) for row in rows)
            return CallToolResult(
                content=[TextContent(type="text", text=result)]
            )
    except McpSecurityError as e:
        logger.warning("get_table_ddl blocked: %s", str(e))
        return _error_response(f"Security Error: {str(e)}")
    except Exception as e:
        logger.error("get_table_ddl failed: %s", str(e), exc_info=True)
        return _error_response(f"Error: {str(e)}\nType: {type(e).__name__}")


@mcp.tool()
def explain_query(query: str) -> CallToolResult:
    """Execute an EXPLAIN plan on a compiled dbt SQL query.

    Send a raw SELECT statement — EXPLAIN is prepended automatically after
    Gatekeeper validation. Returns error if query contains DML/DDL.
    """
    try:
        safe_sql = validate_sql(query)
        if settings.allowed_schema:
            validate_schema(query, settings.allowed_schema)
        with get_cursor() as cursor:
            cursor.execute(f"EXPLAIN {safe_sql}")
            result = [str(row[0]) for row in cursor.fetchall()]
            return CallToolResult(
                content=[TextContent(type="text", text="\n".join(result))]
            )
    except McpSecurityError as e:
        logger.warning("explain_query blocked: %s", str(e))
        return _error_response(f"Security Error: {str(e)}")
    except Exception as e:
        logger.error("explain_query failed: %s", str(e), exc_info=True)
        return _error_response(f"Error: {str(e)}\nType: {type(e).__name__}")


@mcp.tool()
def preview_data(query: str) -> CallToolResult:
    """Fetch a safe data sample (max 50 rows).

    Send a raw SELECT query. LIMIT 50 is injected automatically after
    Gatekeeper validation. Returns error if query contains DML/DDL.
    """
    try:
        safe_sql = validate_sql(query, limit_rows=True)
        if settings.allowed_schema:
            validate_schema(query, settings.allowed_schema)
        with get_cursor() as cursor:
            cursor.execute(safe_sql)
            result = _cursor_to_dicts(cursor)
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2, default=serialize_for_json))]
            )
    except McpSecurityError as e:
        logger.warning("preview_data blocked: %s", str(e))
        return _error_response(f"Security Error: {str(e)}")
    except Exception as e:
        logger.error("preview_data failed: %s", str(e), exc_info=True)
        return _error_response(f"Error: {str(e)}\nType: {type(e).__name__}")


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------


async def security_error_handler(request: Request, exc: McpSecurityError) -> JSONResponse:
    return JSONResponse({"error": str(exc)}, status_code=403)


async def health_check_handler(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "service": "mcp-server"}, status_code=200)


# ---------------------------------------------------------------------------
# App (module-level so uvicorn --reload can import it as src.server:app)
# ---------------------------------------------------------------------------

app = mcp.streamable_http_app()
app.add_route("/health", health_check_handler, methods=["GET"])
app.add_middleware(BearerTokenMiddleware)
app.add_exception_handler(McpSecurityError, security_error_handler)


if __name__ == "__main__":
    host = "0.0.0.0"
    logger.info("Listening on http://%s:9001/mcp", host)
    uvicorn.run(app, host=host, port=9001)

