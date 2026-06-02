# dbt YAML Conventions (Schema Files)

Ensure consistency and discoverability across all dbt documentation files.

## File Naming Standards

| Type | Convention | Location | Example |
| :---- | :---------- | :------- | :------------- |
| **Model Schemas** | `_models.yml` | Same dir as .sql files | `staging/_models.yml` |
| **Source Definitions** | `_sources.yml` | staging/ layer only | `staging/_sources.yml` |
| **Data Tests** | `_tests.yml` or in `_models.yml` | Same dir as models | `marts/_models.yml` |

### Naming Rules

✅ **DO:**

- Use underscore prefix (`_`) for all YAML metadata files
- One `_sources.yml` per source system (e.g., `_sources_spectrum.yml`, `_sources_postgres.yml`)
- Organize models by layer: `staging/_models.yml`, `intermediate/_models.yml`, `marts/_models.yml`

❌ **DON'T:**

- Generic names like `schema.yml` or `models.yml`
- Mix layers in same file (e.g., `stg_dim_schemas.yml`)
- Duplicate model documentation in multiple files

---

## Organization by Layer

### Staging Layer

**Requirements:**
- Mandatory `_sources.yml` - Define all external sources (Spectrum, Postgres, APIs)
- Mandatory `_models.yml` - Document all stg_ models
- **Documentation level:** Minimal (table description + source lineage only)

**Example:**

```yaml
# staging/_sources.yml
sources:
  - name: spectrum_datalake
    schema: onlinemarketing
    tables:
      - name: customer_stats
        description: Raw customer conversion data from Spectrum

# staging/_models.yml
models:
  - name: stg_customer_stats
    description: Cleaned customer conversion metrics
```

### Intermediate Layer

**Requirements:**

- Optional `_models.yml` - Document only if model is reused by 2+ marts
- **Documentation level:** Focus on transformation logic description

**Example:**

```yaml
# intermediate/_models.yml
models:
  - name: int_customer_metrics
    description: |
      Aggregated customer metrics combining conversions and account stats.
      Reused by: fct_customer_analytics_stats, fct_customer_daily_summary
```

### Marts Layer

**Requirements:**

- Mandatory `_models.yml` per subject area - Group models by topic (orders/, customers/, revenue/)
- **Documentation level:** 100% of columns (dimensions + metrics)
- Must include: grain, use case, business owner
- If a fct_ or dim_ model feeds a dashboard directly, its _models.yml description must explicitly name the dashboard, AND it must be registered in an exposures.yml file.

**Organization:**

```
marts/
├── orders/
│   ├── _models.yml  (contains: fct_orders_*, dim_orders_*)
│   ├── fct_orders_daily.sql
│   └── dim_orders.sql
├── customers/
│   ├── _models.yml  (contains: dim_customers, fct_customer_*)
│   └── dim_customers.sql
└── revenue/
    ├── _models.yml  (contains: fct_revenue_*, metrics)
    ├── fct_revenue_daily.sql
    └── fct_revenue_monthly.sql
```

**Example:**

```yaml
# marts/orders/_models.yml
models:
  - name: fct_orders_daily
    description: |
      **Purpose:** Daily order aggregation metrics for analytics and reporting
      **Use Case:** Marketing & sales analytics dashboards
      **Grain:** One row per order_date + order_size_category
      **Refresh:** Full refresh daily
      **Owner:** Analytics Team
```

**Rationale:** Multiple smaller `_models.yml` files prevent single files from becoming unmaintainable (200+ lines) while maintaining single source of truth per subject area.

---

## Documentation Standards

### Model Template

```yaml
models:
  - name: fct_example_stats
    description: |
      **Purpose:** One-sentence summary of business purpose
      **Use Case:** Consumed by [QuickSight dashboard/Data team/External API]
      **Grain:** One row per [entity] + [time period]
      **Refresh:** [Incremental/Full] every [frequency]
      **Owner:** [Team name]
    
    config:
      materialized: incremental
      unique_key: hash_key
      sort: ['dt_date']
      dist: 'dt_date'
    
    columns:
      - name: hash_key
        description: Surrogate key generated from grain columns (unique_key for merge)
        data_type: varchar(32)
        tests:
          - not_null
          - unique
      
      - name: dt_date
        description: Business date (not processing timestamp)
        data_type: date
        tests:
          - not_null
      
      - name: external_account_id
        description: Google Ads account identifier
        data_type: varchar(50)
        tests:
          - not_null
          - relationships:
              to: ref('dim_accounts')
              field: s_external_id
      
      - name: premium_conversions
        description: Count of premium clickouts (ClickoutPremium% actions)
        data_type: integer
```

### Column Documentation Rules

✅ **DO:**

- **Business meaning** (what it represents), NOT technical implementation
- Include `data_type` matching actual DDL (varchar, int, double precision, date)
- Add `tests` for critical columns (PKs, FKs, enums, not nulls)
- Use bullet points for complex metrics

❌ **DON'T:**

- Document auto-generated columns (`updated_at`, `created_at`)
- Use technical jargon without business context
- Leave `data_type` empty

---

## Test Coverage Requirements

### Primary Keys

```yaml
- name: hash_key
  tests:
    - not_null
    - unique
```

### Foreign Keys

```yaml
- name: account_id
  tests:
    - not_null
    - relationships:
        to: ref('dim_accounts')
        field: account_id
```

### Enums
```yaml
- name: brand
  description: Brand identifier (1=Trovit, 2=Mitula, 3=Nestoria)
  data_tests:
    - accepted_values:
        arguments:
          values: [1, 2, 3]
```

### Marts Requirements

- ✅ Minimum 80% of columns documented
- ✅ All PKs and FKs must have tests
- ✅ All metrics must have business description
- ✅ Include grain and use case in model description

---

## Anti-Patterns to Avoid

### ❌ Duplicate Documentation

```yaml
# BAD - fct_model documented in TWO places

analytics/marts/orders/_models.yml      # Contains fct_orders_daily
analytics/marts/fct_orders_daily.yml    # Also contains fct_orders_daily
```

✅ **Solution:** Single source of truth per subject area

```yaml
# GOOD - One location per topic
analytics/marts/orders/_models.yml  # Contains ALL orders-related facts & dimensions
```


### ❌ Confusing Names

```yaml
# BAD
stg_dim_schemas.yml  # Unclear: schemas of what? staging or dim?
schema.yml           # Too generic
models.yml           # Missing underscore prefix
```

✅ **Solution:** Clear, standard names

```yaml
# GOOD
staging/_sources.yml  # Clear: source definitions
staging/_models.yml   # Clear: staging model schemas
marts/_models.yml     # Clear: marts model schemas
```

### ❌ Missing Tests on Critical Columns

```yaml
# BAD - No tests on PK
columns:
  - name: order_id
    description: Primary key
```

✅ **Solution:** Always test PKs

```yaml
# GOOD
columns:
  - name: order_id
    description: Primary key
    tests:
      - not_null
      - unique
```

---

## Validation Checklist

Before committing YAML files:

- [ ] File name uses underscore prefix (`_models.yml`, `_sources.yml`)
- [ ] File is in correct layer directory (staging/intermediate/marts)
- [ ] No duplicate model documentation across files
- [ ] All PKs have `not_null` + `unique` tests
- [ ] All FKs have `relationships` tests
- [ ] Marts have 80%+ columns documented
- [ ] Model description includes grain and use case
- [ ] All `data_type` fields populated

