# Phase-by-Phase Guide

Quick reference for each phase of the workflow.

## Phase 1: Clarification

Ask until clear. Key questions:
- **What** metric/transformation? (count, sum, average, rank?)
- **Why** is this needed? (who uses it, what decision?)
- **When** time period? (all-time, last N, specific dates?)
- **Where** source tables? (single or multiple?)
- **Special logic?** (filters, exclusions, business rules?)

Stop when user's intent is 100% clear.

## Phase 2: Database Discovery

**If MCP available:**
1. `list_tables` → identify source table
2. `get_table_ddl` → understand structure
3. `preview_data` → validate data exists and looks right
4. Confirm with user: "Use this table?"

**If MCP unavailable:** Ask user for table name, columns, row count, data types. Continue normally.

## Phase 3: Design — Layers + Materialization

**3a. Layer complexity:**

| Simple | Complex |
|--------|---------|
| Single table | Multiple tables (joins) |
| Direct aggregation (GROUP BY, SUM, COUNT, AVG) | Window functions (RANK, ROW_NUMBER) |
| No joins | Nested CASE statements |
| → 2 layers (stg → fct) | → 3 layers (stg → int → fct) |

**3b. Materialization (decide per model — see SKILL.md for the full rules):**

| Layer | Default | Override |
|-------|---------|----------|
| staging | `ephemeral` | never |
| intermediate | `view` | `table` if >1M source rows or reused by 2+ marts |
| marts | `table` | `incremental` if append-only & (>5M rows or daily loads) |

Ask the user about update frequency + expected volume if not obvious from MCP. Every generated
model opens with an explicit `{{ config(materialized=...) }}` block; document the choice in the
mart's `meta.materialization` / `meta.materialization_reason`.

## Phase 4: SQL Generation

### Staging (`stg_*`)
```sql
{{ config(materialized='ephemeral') }}

select
  id as fire_id,
  data_hora_gmt as fire_time,
  pais as country,
  risco_fogo as fire_risk
from {{ source('raw_data', 'monthly_fires') }}
where fire_id is not null
```
**Rules:** Rename, cast, simple CASE only. No joins/aggregations.

### Intermediate (`int_*`) [if needed]
```sql
{{ config(materialized='view') }}

select
  date_trunc('month', fire_time) as fire_month,
  country,
  count(*) as incident_count,
  avg(fire_risk) as avg_risk
from {{ ref('stg_raw__fires') }}
group by date_trunc('month', fire_time), country   -- column names, never positional
```
**Rules:** Joins, aggregations, filters. Reusable logic. Never `GROUP BY 1, 2`.

### Fact (`fct_*`)
```sql
{{ config(materialized='table') }}

select
  fire_month,
  country,
  incident_count,
  avg_risk,
  rank() over (order by incident_count desc) as rank
from {{ ref('int_fires_country_month') }}
order by rank
```
**Rules:** Final denormalized table. Define grain explicitly.

## Phase 5: Validation

1. **`dbt compile`** → Check for syntax errors. Report any errors to user.
2. **`explain_query`** → Run on compiled SQL. Report findings:
   - Full table scans?
   - Missing indexes?
   - Estimated cost?
3. **Wait for user approval** before continuing.

## Phase 6: Testing

**YAML (in `_models.yml`):**
```yaml
models:
  - name: fct_fires_monthly
    columns:
      - name: fire_month
        tests: [not_null, unique]
      - name: incident_count
        tests: [not_null]
```

**Acceptance test** — one per fact, at `tests/<model>/acceptance_<model>.sql`. It must return
rows **only when an assertion fails** (dbt fails the test if any rows come back). Use the
multi-assertion template in SKILL.md (has_rows, no_nulls on keys, metric sanity, grain
uniqueness). Skeleton:

```sql
with model as (select * from {{ ref('fct_fires_monthly') }}),
check_metric_range as (
    select 'check_metric_range' as assertion, count(*) as failing_rows
    from model
    where avg_risk < 0 or avg_risk > 1
    having count(*) > 0
)
-- … UNION ALL more checks …
select * from check_metric_range
```

Run: `docker exec dbt-dev dbt test` → all must PASS.

## Phase 7: Deploy

1. `dbt run` → Materialize all models
2. Report completion with file locations
3. User confirms: "Ready to deploy?"

---

## If Something Fails

| Error | Action |
|-------|--------|
| `dbt compile` fails | Show error to user, fix SQL, recompile |
| `explain_query` shows full scan | Report to user, wait for approval |
| `dbt test` fails | Debug, fix test or SQL, retest |
| User says "change X" | Go back to Phase 4, regenerate, revalidate |
