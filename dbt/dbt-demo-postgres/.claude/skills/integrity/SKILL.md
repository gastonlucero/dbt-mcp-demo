---
name: integrity
description: >
  Ensures consistent dbt architecture: SIM layering (Staging→Intermediate→Marts), naming conventions, and YAML documentation standards. Eliminates sprawl, maintains single source of truth.
user-invocable: false
allowed-tools: "Bash(dbt *), Read, Write, Edit"
version: 1.0
context: dbt + Postgres
objective: Enforce consistent dbt conventions across the project.
 
---

## Invocation Triggers

Load this skill when:
- Creating new `.sql` or `.yml` files in `models/`
- Refactoring models
- Documenting schemas

---

## Resources

| Resource | Use Case |
|----------|----------|
| **layering.md** | Layer architecture: Staging (1:1 source) → Intermediate (reusable logic) → Marts (final tables) |
| **naming-conventions.md** | Column/model naming: PKs as `object_id`, timestamps as `_at`, booleans as `is_/has_` |
| **yaml-conventions.md** | YAML documentation: `_models.yml`, `_sources.yml`, tests, grain definitions |

---

## How to Apply

**When creating/reviewing code:**
1. Read this file (overview)
2. Load relevant resource(s) from table above
3. Apply conventions
4. Validate against critical rules below

---

## 🚨 Critical Rules (Always Enforce)

These rules apply universally, regardless of which resource is loaded:

1. **No logic in staging** - Only renaming and type casting
2. **No `SELECT *`** - Explicit column names required
3. **Underscore prefix for YAML** - `_models.yml`, never `schema.yml`
4. **PKs always tested** - `not_null` + `unique` mandatory
5. **Marts 80% documented** - Include grain, use case, owner
6. **`GROUP BY` by column name only** - Never use positional references (e.g. `GROUP BY 1, 2`); always use explicit column names (e.g. `GROUP BY order_date, customer_id`)

---

## Quick Reference

✅ **MUST DO:**
- Staging: Only rename + cast (no joins/logic)
- No `SELECT *` in final models
- YAML files: `_models.yml`, `_sources.yml` (underscore prefix)
- PKs always tested: `not_null` + `unique`
- Marts 80%+ documented with grain + use case

❌ **NEVER:**
- Business logic in staging layer
- `id` as primary key (use `object_id`)
- `schema.yml` (use `_models.yml` or `_sources.yml`)
- Skip PK/FK tests
- `GROUP BY 1, 2, ...` — always use column names, never positions