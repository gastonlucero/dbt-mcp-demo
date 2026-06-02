# dbt Analytics Project + MCP Server

A professional dbt project integrated with a PostgreSQL Model Context Protocol (MCP) server for safe, read-only schema introspection and data exploration.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Verify MCP Server Connection
```bash
curl -H "Authorization: Bearer test-token" \
  http://localhost:9001/mcp/
```

Expected response: `200 OK`

### 3. Verify PostgreSQL Connection
```bash
dbt debug
```

Expected output: `All checks passed!`

### 4. Run Models
```bash
dbt run
dbt test
dbt docs generate
dbt docs serve
```

Then open http://localhost:8000 to explore the documentation.

---

## 📁 Project Structure

```
dbt-project/
├── dbt_project.yml              # dbt configuration
├── profiles.yml                 # Database connection profile
├── requirements.txt             # Python dependencies
│
├── models/
│   ├── _sources.yml             # Source table definitions
│   ├── base/                    # Raw models (minimal transforms)
│   ├── staging/                 # Staging models (1NF transforms)
│   └── marts/                   # Business logic models
│
├── macros/
│   └── mcp_connector/           # Macros for MCP integration
│       ├── query_mcp_tool.sql
│       ├── get_table_schema.sql
│       └── preview_table_data.sql
│
├── tests/
│   ├── generic/                 # Custom test macros
│   └── data_tests/              # SQL data quality tests
│
├── .claude/
│   ├── settings.json            # Claude Code MCP config
│   └── CLAUDE.md                # Claude development guide
│
└── README.md                    # This file
```

---

## 🔌 MCP Server Integration

### Available Tools
The MCP server at `http://localhost:9001/mcp/` provides 4 tools:

1. **list_tables(schema_name)**
   - Discover all tables in a schema
   - Returns: Table names and types

2. **get_table_ddl(schema, table)**
   - Get table structure/schema
   - Returns: Column names, types, nullability

3. **preview_data(query)**
   - Sample data from a query
   - Max 50 rows, safe execution
   - Returns: JSON with data

4. **explain_query(query)**
   - Analyze query performance
   - Returns: Query execution plan

### How to Use with Claude Code

1. Open Claude Code in this directory
2. Claude automatically detects MCP server from `.claude/settings.json`
3. Use tools to explore data before writing models
4. Claude can generate optimized SQL and documentation

### Example: Exploring a Table
```
Claude: "List all tables in analytics schema"
→ Uses list_tables("analytics")
→ Returns: ["sample_orders", ...]

Claude: "What's the structure of sample_orders?"
→ Uses get_table_ddl("analytics", "sample_orders")
→ Returns: [{"column_name": "order_id", "data_type": "integer", ...}]

Claude: "Show me a sample of the data"
→ Uses preview_data("SELECT * FROM analytics.sample_orders")
→ Returns: [{"order_id": 1, "customer_id": 42, "amount": 99.99}]
```

---

## 📊 Model Layers

### Base Models
- **Location**: `models/base/`
- **Purpose**: Read raw data with minimal transformations
- **Materialization**: Tables
- **Example**: `base_analytics__sample_orders.sql`
  - Selects all columns from source table
  - Adds `dbt_load_timestamp`
  - Minimal filtering

### Staging Models
- **Location**: `models/staging/`
- **Purpose**: Clean, standardize, apply business logic
- **Materialization**: Views
- **Example**: `stg_analytics__sample_orders.sql`
  - Filters out nulls
  - Renames columns for clarity
  - Adds derived columns (categorizations)
  - Applies data quality rules

### Mart Models
- **Location**: `models/marts/`
- **Purpose**: Aggregate and optimize for analytics
- **Materialization**: Tables
- **Examples**:
  - `fct_orders_daily.sql` - Daily aggregation of orders
  - `dim_customers.sql` - Dimension table for customers

---

## 🧪 Testing

### Running Tests
```bash
# All tests
dbt test

# Specific model
dbt test -s stg_analytics__sample_orders

# Specific test
dbt test -s not_null_stg_analytics__sample_orders_order_id

# Show detailed output
dbt test --debug
```

### Test Types

**Generic Tests** (built-in)
- `not_null` - Column has values
- `unique` - No duplicate values
- `accepted_values` - Values in whitelist
- `relationships` - Foreign key validation

**Data Tests** (custom SQL)
- Custom SQL queries in `tests/data_tests/`
- Return 0 rows if test passes

### Example: Add a Test
```yaml
models:
  - name: stg_analytics__sample_orders
    columns:
      - name: order_id
        tests:
          - not_null
          - unique
```

---

## 📖 Documentation

### Generate Docs
```bash
dbt docs generate
dbt docs serve
```

Open http://localhost:8000 to view:
- Model descriptions
- Column definitions
- Data lineage diagram
- Relationships
- Source table information

### Add Documentation
```yaml
models:
  - name: fct_orders_daily
    description: |
      Daily aggregation of orders by size category.
      Includes metrics for order count, customer count, and totals.

    columns:
      - name: order_date
        description: Date of the order (YYYY-MM-DD)

      - name: order_size_category
        description: Size category of the order (large, medium, small, invalid)
```

---

## 🔐 Security & Access

- **Read-Only**: All access is read-only (no writes/deletes)
- **Token Auth**: Bearer token required for MCP server
- **Schema Isolation**: Can restrict access to specific schema
- **Query Timeout**: 15-second timeout per query
- **Row Limit**: Max 50 rows in preview_data()

---

## 🛠️ Development Workflow

### 1. Explore Data
```bash
# Use Claude Code or MCP tools to understand source data
# Claude: "What tables are in analytics schema?"
```

### 2. Create Base Model
```sql
-- models/base/base_analytics__<table>.sql
SELECT * FROM {{ source('analytics', '<table>') }}
```

### 3. Create Staging Model
```sql
-- models/staging/stg_analytics__<table>.sql
SELECT
    col1,
    col2,
    ...
FROM {{ ref('base_analytics__<table>') }}
WHERE col1 IS NOT NULL
```

### 4. Add YAML Documentation
```yaml
# models/staging/stg_analytics__<table>.yml
models:
  - name: stg_analytics__<table>
    description: ...
    columns:
      - name: col1
        description: ...
        tests:
          - not_null
```

### 5. Run & Test
```bash
dbt run
dbt test
```

### 6. Document & Review
```bash
dbt docs generate
dbt docs serve
```

---

## 🐛 Troubleshooting

### "dbt debug" fails
```
✓ PostgreSQL running on localhost:5432?
✓ Correct credentials in profiles.yml?
✓ .env file configured?
```

### "Source not found"
```
✓ Table exists in PostgreSQL?
✓ Correct schema in _sources.yml?
✓ Use list_tables("schema") via Claude/MCP?
```

### "Test failed"
```
✓ Check data with preview_data() via Claude
✓ Review test expectations
✓ Adjust transformation or test criteria
```

### Models not showing in docs
```bash
dbt parse  # Refresh schema
dbt docs generate
```

---

## 📚 Key Commands

| Command | Purpose |
|---------|---------|
| `dbt init` | Initialize new dbt project |
| `dbt debug` | Verify database connection |
| `dbt run` | Execute all models |
| `dbt run -s model_name` | Run specific model |
| `dbt test` | Run all tests |
| `dbt compile` | Compile SQL without executing |
| `dbt snapshot` | Create table snapshot |
| `dbt seed` | Load CSV data |
| `dbt docs generate` | Generate documentation |
| `dbt docs serve` | Serve docs locally |
| `dbt freshness` | Check source freshness |

---

## 🎯 Best Practices

1. **Use ref() and source()**
   - `ref()` for dbt models
   - `source()` for external tables

2. **Layer Your Transformations**
   - Base: minimal transforms
   - Staging: clean & standardize
   - Marts: aggregate & optimize

3. **Test Everything**
   - Every source table
   - Key columns (PK, FK)
   - Data quality assumptions

4. **Document as You Go**
   - Add YAML descriptions
   - Link related models
   - Explain complex logic

5. **Version Control**
   - Commit YAML, SQL, config
   - Tag stable versions
   - Use git branches for features

---

## 📝 Configuration

### profiles.yml
- `dev`: Local PostgreSQL (localhost:5432)
- `prod`: Production PostgreSQL (via env vars)

### dbt_project.yml
- `models.dbt_analytics.base`: materialized as tables
- `models.dbt_analytics.staging`: materialized as views
- `models.dbt_analytics.marts`: materialized as tables

### .env
```
DBT_POSTGRES_HOST=localhost
DBT_POSTGRES_PORT=5432
DBT_POSTGRES_DATABASE=postgres
DBT_POSTGRES_USER=postgres
DBT_POSTGRES_PASSWORD=postgres
MCP_SERVER_URL=http://localhost:9001/mcp/
MCP_AUTH_TOKEN=test-token
```

---

## 🔗 Resources

- [dbt Documentation](https://docs.getdbt.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [MCP Protocol Spec](https://spec.modelcontextprotocol.io/)
- [Claude Code](https://claude.com/claude-code)

---

## 📞 Support

For questions or issues:
1. Check the `.claude/CLAUDE.md` guide
2. Review dbt documentation
3. Verify MCP server is running
4. Check PostgreSQL connection with `dbt debug`

---

**Created**: 2026-05-12  
**Version**: 1.0.0  
**Stack**: dbt + PostgreSQL + MCP Server
