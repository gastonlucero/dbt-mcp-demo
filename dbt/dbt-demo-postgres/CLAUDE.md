# CLAUDE.md — dbt-demo-postgres

A dbt analytics project with PostgreSQL backend, organized by **SIM pattern** (Staging → Intermediate → Marts).

---

## ⚠️ Execution: everything runs inside Docker

This project's dbt and database **only exist inside containers** — they are not installed on
the host. Never run `dbt`, `psql`, or related commands locally; they will fail or hit the wrong
environment. Always go through Docker:

```bash
docker exec dbt-dev <dbt command>          # dbt (container: dbt-dev)
docker exec mcp-postgres-dev psql -U postgres -c "..."   # SQL (container: mcp-postgres-dev)
```

`docker exec` takes the **container** name (`dbt-dev`, `mcp-postgres-dev`). `docker-compose`
subcommands take the **service** name (`dbt`, `postgres`). The repo-level `make` targets
(`make dbt-run`, `make dbt-test`, `make dbt-shell`, …) wrap these for you.

The command examples below omit the `docker exec dbt-dev` prefix **only** when you are already
inside an interactive shell opened with `make dbt-shell`. From anywhere else, add the prefix.

---

## Quick Start

```bash
docker exec dbt-dev dbt debug          # Verify PostgreSQL connection
docker exec dbt-dev dbt run            # Execute all models
docker exec dbt-dev dbt test           # Run all tests
docker exec dbt-dev dbt docs generate  # Generate documentation
# equivalently: make dbt-debug / make dbt-run / make dbt-test / make dbt-docs
```

---

## Project Structure

```
models/
├── staging/          # 1:1 source reflection (ephemeral)
│   └── <subject>/
│       ├── _sources.yml
│       ├── _models.yml
│       └── stg_*.sql
├── intermediate/     # Reusable logic (views)
│   └── <subject>/
│       ├── _models.yml
│       └── int_*.sql
└── marts/           # Final tables for BI (materialized)
    └── <subject>/
        ├── _models.yml
        ├── fct_*.sql
        └── dim_*.sql
```

**Layers:**
- **Staging** (`stg_`): Rename columns, cast types. No joins/logic.
- **Intermediate** (`int_`): Reusable transformations. For 2+ marts.
- **Marts** (`fct_`, `dim_`): Final denormalized tables. Well-documented.

---

## Key Commands

Prefix each with `docker exec dbt-dev` (or run inside `make dbt-shell`):

| Task | Command |
|------|---------|
| Run specific model | `docker exec dbt-dev dbt run -s model_name` |
| Test specific model | `docker exec dbt-dev dbt test -s model_name` |
| View compiled SQL | `docker exec dbt-dev dbt show -s model_name` |
| Verbose debugging | `docker exec dbt-dev dbt run --debug` |
| Open interactive shell | `make dbt-shell` |

---

## Conventions (See `integrity` Skill)

**Naming:**
- Models: `stg_domain__entity`, `fct_entity_grain`, `dim_entity`
- PKs: `object_id` (never just `id`)
- Timestamps: `created_at`, `updated_at`
- Booleans: `is_active`, `has_subscription`, `does_qualify`

**YAML Files:**
- Use `_models.yml` and `_sources.yml` (underscore prefix)
- Staging: minimal docs, mandatory sources
- Marts: 80%+ columns documented, with grain + use case

**Tests:**
- All PKs: `not_null` + `unique`
- All FKs: `relationships`
- Enums: `accepted_values`

For complete conventions, see: `.claude/skills/integrity/resources/`

---

## Common Workflows

> **Fastest path:** use the `dbt-mcp-developer` skill — it explores the DB via MCP, picks
> layering + materialization, and generates SQL + YAML + acceptance tests. The manual steps
> below are the same flow by hand.
>
> The `dbt …` lines assume you're inside `make dbt-shell`. From a host shell, prefix each with
> `docker exec dbt-dev`.

### Create a Staging Model
```bash
# 1. Explore data
dbt show -s source_table

# 2. Create models/staging/<subject>/stg_*.sql
# 3. Add _models.yml and _sources.yml
# 4. Run and test
dbt run -s stg_*
dbt test -s stg_*
```

### Create a Mart
```bash
# 1. Design grain (daily, monthly, per customer, etc.)
# 2. Create models/marts/<subject>/fct_*.sql or dim_*.sql
# 3. Add comprehensive _models.yml (80%+ columns documented)
# 4. Add tests (PKs, FKs, business rules)
# 5. Run and test
dbt run -s fct_*
dbt test -s fct_*
```

---

## Troubleshooting

All commands below run via `docker exec dbt-dev …` (or inside `make dbt-shell`).

| Error | Fix |
|-------|-----|
| `dbt debug` fails | Check containers are up (`make info`); verify the `postgres` service is healthy and credentials in `.env` |
| "Source not found" | Verify table exists: `docker exec mcp-postgres-dev psql -U postgres -c "SELECT * FROM schema.table LIMIT 1"` |
| Test failed | `docker exec dbt-dev dbt show -s model_name` to see actual data, then adjust transformation or test |
| Model returns 0 rows | Debug filter logic, date ranges, joins. Use `docker exec dbt-dev dbt run -s model_name --debug` |
| `docker exec ... no such container` | Stack not running — start it with `make dev` |

---

## Resources

- **dbt Docs**: https://docs.getdbt.com/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Conventions Skill**: `.claude/skills/integrity/`
- **Project README**: `README.md`
