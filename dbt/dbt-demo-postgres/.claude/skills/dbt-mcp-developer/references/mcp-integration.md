# MCP Server: Available vs Unavailable

## If MCP Server is Available

MCP provides 4 read-only tools for safe database exploration:

| Tool | What it does |
|------|-----------|
| `list_tables` | List tables in schema |
| `get_table_ddl` | Get table structure (columns, types) |
| `preview_data` | Show sample rows (max 50) |
| `explain_query` | Analyze query performance |

**Flow:**
1. Check server status → `✅ MCP server responding at http://localhost:9001/mcp/`
2. `list_tables` → Find source table
3. `get_table_ddl` → Understand structure
4. `preview_data` → Validate data exists
5. Confirm with user: "Use this table?"
6. After SQL generation: `explain_query` → Report performance findings
7. User approves recommendations → Continue

## If MCP Server is Unavailable

**Detect:** 
```
Agent: "Checking MCP... ❌ Cannot connect"
Agent: "Switching to manual mode. I'll ask for information."
```

**Request from user (in order):**

1. **Table name & schema**
   - Example: `raw_data.monthly_fires`

2. **Columns with types**
   - Example: `id (UUID), data_hora_gmt (timestamp), risco_fogo (numeric)`

3. **Row count & data quality**
   - Example: `1.2M rows, id always populated, pais can be null`

4. **EXPLAIN ANALYZE (optional)**
   - If user can run: `EXPLAIN ANALYZE SELECT * FROM table LIMIT 1000;`

**Then proceed normally:**
- Design layers
- Generate SQL
- Create YAML + tests
- Skip `explain_query` (no MCP)
- Ask user to run `dbt compile` locally

## Manual Mode Checklist

✅ **Be specific with column types**
- ❌ "id is a number"
- ✅ "id is UUID"

✅ **Identify date columns** (for time-based grouping)
- "Use data_hora_gmt for monthly aggregation"

✅ **Report data quality issues**
- "Column X has ~5% nulls"
- "Some future-dated records (data issue)"

✅ **Share EXPLAIN results if possible** (helps agent optimize)

## When MCP Comes Back Online

1. Agent can re-validate SQL with `explain_query`
2. Agent can optimize based on performance findings
3. Can regenerate docs

## Security

- Bearer token auth (in `.env`)
- All queries read-only (AST-validated)
- 15-second query timeout
- Manual mode: user input is trusted (be careful with SQL)
