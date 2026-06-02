---
name: dbt-mcp-developer
description: |
  Build complete dbt models from natural language. Agent explores database via MCP, decides layer complexity (stg→fct or stg→int→fct), generates SQL+YAML+tests, validates with dbt compile and explain_query tool, and creates production-ready files. Use whenever user describes what they want to calculate or transform.
---

## Environment

**All commands execute inside Docker:**
- `dbt compile`, `dbt test`, `dbt run` — all inside dbt container
- `explain_query` calls — via MCP server (running in Docker)
- File writes — to `/app/dbt-demo-postgres/models/` (mounted volume)
- **Never use local machine commands** — everything through Docker

## Docker Commands (ALWAYS USE)

❌ **NEVER** run locally:
```bash
dbt run
dbt compile
dbt test
psql ...
```

✅ **ALWAYS** use docker exec:
```bash
docker exec dbt-dev dbt run
docker exec dbt-dev dbt compile
docker exec dbt-dev dbt test
docker exec dbt-dev dbt show -s model_name
docker exec mcp-postgres-dev psql -U postgres -c "SELECT ..."
```

**Container names:**
- `dbt-dev` = dbt container
- `mcp-postgres-dev` = PostgreSQL container

## The Flow

| Phase | Action | MCP Tools | Output |
|-------|--------|-----------|--------|
| 1. Clarify | Ask questions until requirements are clear | — | Understand: what, why, when, where |
| 2. Discover | Explore database schema | `list_tables` → `get_table_ddl` → `preview_data` | Confirm table structure & data |
| 3. Design | Decide layers + **materialization for every model** | — | Architecture + materialization plan |
| 4. Generate | Load `integrity` skill → write SQL + YAML + tests | — | Files ready for compilation |
| 5. Validate | `dbt compile` + **`explain_query`** | **`explain_query` (REQUIRED)** | Performance validated, user approves |
| 6. Test | `dbt test` → all tests pass | — | Quality verified |
| 7. Deploy | `dbt run` → models materialized | — | Complete |

## Phase 3 — Design: Materialization Decision

Materialization is not cosmetic — it determines storage cost, query latency, and pipeline complexity. Decide it explicitly for every model before writing a single line of SQL.

### Decision rules

| Layer | Default | Override to `table` when… | Override to `incremental` when… |
|-------|---------|--------------------------|----------------------------------|
| **staging** (`stg_`) | `ephemeral` | Never — staging should never persist | — |
| **intermediate** (`int_`) | `view` | Source > ~1M rows **or** model is referenced by 2+ downstream marts | — |
| **marts** (`fct_`, `dim_`) | `table` | — | Source is append-only **and** (> 5M rows **or** loaded daily/hourly) |

### How to gather the missing signals

After MCP exploration you'll know row counts and column shapes. What you won't know yet:

- **Update frequency** — is the source table appended daily? replaced in full? never updated?
- **Expected growth** — will this table grow to millions of rows, or stay small?

If these aren't obvious from `preview_data` (e.g. timestamps show daily appends) or from context the user already provided, **ask before designing**:

> "Two quick questions before I design the models:
> 1. How often is `<source_table>` updated — daily load, real-time append, or periodic full replace?
> 2. Roughly how many rows do you expect in 6–12 months?"

Skip the questions only if the answers are already clear (e.g. the user said "daily CSV load" earlier, or row counts from MCP are already in the millions with timestamps that show appends).

### Show your decision

Before generating files, present the materialization plan to the user:

```
Materialization plan:
  stg_fires__monthly_fires      → ephemeral  (no storage, always fresh from source)
  fct_fires__by_country_month   → table      (370K rows, full rebuild is fast)
```

If you're choosing `incremental`, also state the unique_key and strategy (e.g. `delete+insert` on `fire_event_id`).

### Inject the config block into every SQL model

Every model file must open with an explicit `{{ config(...) }}` block — never rely on `dbt_project.yml` defaults alone, because defaults are invisible to anyone reading the model file.

```sql
-- staging (ephemeral)
{{ config(materialized='ephemeral') }}

-- intermediate (view)
{{ config(materialized='view') }}

-- mart (table)
{{ config(materialized='table') }}

-- mart (incremental)
{{ config(
    materialized='incremental',
    unique_key='fire_event_id',
    incremental_strategy='delete+insert'
) }}
```

### Document the decision in YAML

Add `meta.materialization` and `meta.materialization_reason` to every mart's `_models.yml` entry so future developers understand why the choice was made:

```yaml
meta:
  grain: "One row per fire event per day."
  use_case: "Daily fire monitoring dashboard."
  materialization: incremental
  materialization_reason: >
    Source appends ~50K rows daily. Full rebuild would scan 5M+ rows on every run.
    Incremental on fire_event_id keeps each run under 1 minute.
```

## Phase 4 — Generate: Apply Integrity Conventions

Before writing any SQL or YAML, load the `integrity` skill and apply its rules to every file you generate. This is not optional — it's what keeps the project consistent as it grows.

```
Load skill: .claude/skills/integrity/SKILL.md
```

The most common violations to watch for (from `integrity`):

| Rule | Example violation | Correct |
|------|-------------------|---------|
| No logic in staging | `JOIN` or `CASE` in `stg_` | Only rename + cast |
| No `SELECT *` in final models | `select * from int_...` in fct_ | Explicit column list |
| PKs always tested | Missing `not_null` + `unique` on `fire_event_id` | Add both tests |
| GROUP BY by name | `GROUP BY 1, 2, 3` | `GROUP BY country, municipality` |
| YAML underscore prefix | `schema.yml` | `_models.yml`, `_sources.yml` |
| Marts 80%+ documented | Columns without description | Add description to every column |

For the full naming rules (PKs as `object_id`, timestamps as `_at`, booleans as `is_/has_`) and YAML conventions, read the relevant resource files in `.claude/skills/integrity/resources/`.

## What to Generate

**SQL Models** (`models/{domain}/{layer}/`)
- Every model opens with an explicit `{{ config(materialized=...) }}` block
- Staging: `ephemeral` — rename + clean only, no logic
- Intermediate: `view` (default) or `table` per decision above
- Fact/Dim: `table` (default) or `incremental` per decision above
- MUST compile cleanly, MUST validate with explain_query tool

**YAML** (`_models.yml`)
- Description, columns, tests (`not_null`, `unique`, `relationships`)
- For marts: `meta.grain`, `meta.use_case`, `meta.materialization`, `meta.materialization_reason`

**Acceptance Tests** (`tests/<model_name>/acceptance_<model_name>.sql`)

Every `fct_` model requires one acceptance test file. The file lives at:
```
tests/<model_name>/acceptance_<model_name>.sql
```

The test is a SQL query that **returns rows only when something is wrong**. dbt fails the test if any rows are returned.

Write 3–5 assertions covering:
1. **Row count** — the model has at least 1 row
2. **No nulls on key columns** — country, municipality, and the main metric are never null
3. **Metric sanity** — totals or averages are within a sensible range (e.g. fire count ≥ 0, risk score between 0 and 1)
4. **Grain uniqueness** — the declared grain has no duplicates

**Template:**
```sql
-- Acceptance test: <model_name>
-- Returns rows if any assertion fails. Zero rows = all good.

with model as (
    select * from {{ ref('<model_name>') }}
),

-- 1. Must have at least one row
check_has_rows as (
    select 'check_has_rows' as assertion, count(*) as failing_rows
    from model
    having count(*) = 0
),

-- 2. Key columns must never be null
check_no_nulls as (
    select 'check_no_nulls' as assertion, count(*) as failing_rows
    from model
    where country is null
       or municipality is null
       or <main_metric> is null
    having count(*) > 0
),

-- 3. Metric sanity
check_metric_range as (
    select 'check_metric_range' as assertion, count(*) as failing_rows
    from model
    where <main_metric> < 0
    having count(*) > 0
),

-- 4. Grain uniqueness
check_grain as (
    select 'check_grain_uniqueness' as assertion, count(*) as failing_rows
    from (
        select <grain_columns>, count(*) as n
        from model
        group by <grain_columns>
        having count(*) > 1
    ) dupes
    having count(*) > 0
)

select * from check_has_rows
union all select * from check_no_nulls
union all select * from check_metric_range
union all select * from check_grain
```

Replace `<model_name>`, `<main_metric>`, and `<grain_columns>` with the actual values for each model.

**Generic YAML tests** (`_models.yml`)
- `not_null` and `unique` on all PKs
- `relationships` on all FKs
- `accepted_values` on enum columns

## Critical Rules

✅ **MUST DO:**
- **Phase 2:** Call `list_tables` → `get_table_ddl` → `preview_data` (always)
- **Phase 3:** Decide and show materialization for every model before writing SQL
- **Phase 5:** Call `explain_query` on compiled SQL (always)
- Ask about update frequency + volume if not obvious from MCP data
- Execute `dbt compile` → fix any errors
- Report explain_query findings to user + wait for approval
- Write clean, commented SQL with explicit `{{ config(...) }}` in every file
- All tests PASS before deployment

❌ **NEVER:**
- Skip Phase 2 MCP exploration
- Skip Phase 3 materialization decision
- Skip Phase 5 explain_query validation
- Write SQL without seeing actual data
- Rely on dbt_project.yml defaults without an explicit config block in the model
- Run dbt run without user confirmation
- Generate .md documentation

## Examples

**Simple:** "Monthly fire counts + avg risk"  
→ `stg_raw__fires` → `fct_fires_monthly`

**Complex:** "Top 10 months by incidents, broken down by country + risk"  
→ `stg_raw__fires` → `int_fires_country_month` → `fct_fires_monthly_country_risk`

## MCP Requirements

**MCP Server MUST be available:**
- Phase 2 exploration requires: `list_tables`, `get_table_ddl`, `preview_data`
- Phase 5 validation requires: `explain_query`

If MCP unavailable: stop and report "❌ MCP server not responding". See `references/mcp-integration.md` for manual fallback.

## References

- Detailed workflow: `references/workflow-detailed.md`
- MCP details: `references/mcp-integration.md`
- Troubleshooting: `references/troubleshooting.md`
- **Conventions (load in Phase 4):** `.claude/skills/integrity/SKILL.md`
  - Layering rules: `integrity/resources/layering.md`
  - Naming conventions: `integrity/resources/naming-conventions.md`
  - YAML standards: `integrity/resources/yaml-conventions.md`
