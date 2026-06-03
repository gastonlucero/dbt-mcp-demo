# CLAUDE.md

Repo-wide guidance for **dbt-demo-mcp**: an analytics stack that pairs a read-only PostgreSQL
**MCP server** (Python/FastMCP) with a **dbt** project, orchestrated by Docker. The MCP server
gives agents safe DB tools (schema inspection, preview, `EXPLAIN`) behind AST-based SQL validation.

### Two CLAUDE.md files, by scope

| File | Scope |
|------|-------|
| `CLAUDE.md` (this) | Repo-wide: Docker, MCP server, stack commands |
| `dbt/dbt-demo-postgres/CLAUDE.md` | dbt subproject: commands, SIM layering, conventions, model workflows |

Keep dbt-specific guidance in the subproject file (auto-loaded when working under `dbt/…`). The
dbt skills live in `dbt/dbt-demo-postgres/.claude/skills/` (`dbt-mcp-developer`, `integrity`).

---

## ⚠️ Everything runs in Docker

dbt and Postgres only exist in containers — never run `dbt`/`psql` on the host. Mind the
**container vs service** name split (this bites people):

| Service (for `docker-compose`) | Container (for `docker exec`) | Port |
|--------------------------------|-------------------------------|------|
| `postgres` | `mcp-postgres-dev` | 5432 |
| `mcp-server` | `mcp-server-dev` | 9001 |
| `dbt` | `dbt-dev` | — |

```bash
docker exec dbt-dev dbt <cmd>                              # dbt
docker exec mcp-postgres-dev psql -U postgres -c "..."     # SQL
```

The compose `environment:` blocks override host-related vars at runtime (the `dbt` service
points `DBT_POSTGRES_HOST` at the `postgres` service by name), so `.env` values are defaults,
not the final word. Service names are used over `host.docker.internal` so the stack works on
Linux CI too.

---

## Stack commands (Makefile)

```bash
make dev / dev-build      # Start stack (foreground — streams logs, blocks the terminal)
make dbt-run / dbt-test / dbt-docs / dbt-debug / dbt-shell
make logs-dbt / logs-mcp / logs-postgres
make stop                 # stop containers (kept)
make down                 # remove containers + network (volume kept)
make clean                # down + delete postgres volume (⚠️ wipes all data)
make info                 # status, network, volumes
```

`make` targets wrap the right container/service names for you — prefer them.

---

## MCP server

- **Endpoint:** JSON-RPC over Streamable HTTP at `POST /mcp` (note: `/mcp/` 307-redirects).
  Requires `Authorization: Bearer <AUTH_TOKEN>` and `Accept: application/json, text/event-stream`.
- **Gatekeeper** (`mcp-server/src/logic/gatekeeper.py`): validates SQL via sqlglot AST — allows
  only `SELECT`/`EXPLAIN`/`SHOW`, blocks all DML/DDL **and `UNION`**, auto-injects `LIMIT 50`,
  15s statement timeout. Violations → `McpSecurityError` → HTTP 403.
- **Auth/config:** `auth/middleware.py` (Bearer), `config.py` (pydantic-settings). `DEV_MODE=true`
  skips auth. `ALLOWED_SCHEMA` optionally pins one schema (unset = any).

The four tools are `list_tables`, `get_table_ddl`, `preview_data`, `explain_query`. Explore the
DB through the API (handy shell helper):

```bash
mcp() {  # mcp <tool> <json-args>
  curl -s -X POST http://localhost:9001/mcp \
    -H "Authorization: Bearer test-token" \
    -H "Accept: application/json, text/event-stream" \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"$1\",\"arguments\":$2}}"
}
mcp list_tables   '{"schema_name":"public"}'
mcp get_table_ddl '{"schema":"raw_data","table":"monthly_fires"}'
mcp preview_data  '{"query":"SELECT * FROM raw_data.monthly_fires"}'   # auto LIMIT 50
mcp explain_query '{"query":"SELECT pais, count(*) FROM raw_data.monthly_fires GROUP BY pais"}'
```

Run standalone (host) with a project-root `.env`: `python3 -m uvicorn src.server:app --port 9001`.
Tests: `cd mcp-server && python3 -m pytest tests/` (auth, gatekeeper, e2e).

---

## Data & layout

- Source data: `raw_data.monthly_fires` (~384k satellite fire detections, loaded from CSVs by
  `docker/init.sql`). dbt models materialize into `public`.
- dbt models are organized by layer → subject area (`models/{staging,intermediate,marts}/fires/`).
  See the subproject CLAUDE.md for conventions and the model-development workflow.

```
mcp-server/src/   server.py · config.py · auth/middleware.py · logic/{database,gatekeeper}.py
dbt/              Dockerfile.dbt · entrypoint.sh · dbt-demo-postgres/{models,macros,tests,.claude}
docker/           docker-compose.yml · Dockerfile · init.sql · *.csv
```

> ⚠️ The `macros/mcp_connector/` macros (`query_mcp_tool`, …) are **demo stubs** — they only
> `log()`, they do not call the MCP server. Use the HTTP API directly (above).

---

## Troubleshooting

- **Stack/DB:** `make info` (status), `make dbt-debug` (dbt↔Postgres), `make logs-postgres`.
- **MCP up?** `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:9001/health` → `200`.
- **`docker exec … no such container`:** stack isn't running — `make dev`.
- **dbt model:** `docker exec dbt-dev dbt run -s <model> --debug` / `dbt show -s <model>`.
