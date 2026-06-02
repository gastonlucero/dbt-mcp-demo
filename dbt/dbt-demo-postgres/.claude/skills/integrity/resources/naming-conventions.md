# Naming Conventions (Strict Enforcement)

AI should automatically suggest renames if code violates these rules.

## Standard Patterns

| Entity Type | Rule | Example                         | Counter-Example |
| :--- | :--- |:--------------------------------| :--- |
| **Model Name** | Pluralized snake_case | `stg_payment_methods`           | `stg_PaymentMethod` ❌ |
| **Primary Key** | `<object>_id` | `customer_id`                   | `id` ❌ |
| **Timestamps** | Ends in `_at` (UTC) | `created_at`, `updated_at`      | `create_time` ❌ |
| **Dates** | Ends in `_date` | `report_date`, `cohort_date`    | `dt` ❌ |
| **Booleans** | Prefixed with `is_`, `has_`, `does_` | `is_active`, `has_subscription` | `active` ❌ |
| **Currency** | Suffix with currency code | `amount_eur`, `tax_cents`       | `amount` ❌ |
| **Counts** | Prefix with `n_` or `count_` | `n_orders`, `count_clicks`      | `orders` ❌ |

## Model Prefixes

| Prefix | Layer | Example | Purpose |
|:-------|:------|:--------|:--------|
| `stg_` | Staging | `stg_stripe_payments` | Raw source cleanup |
| `int_` | Intermediate | `int_customer_metrics` | Reusable logic |
| `fct_` | Marts | `fct_daily_revenue` | Event-based facts |
| `dim_` | Marts | `dim_customers` | Descriptive dimensions |

## Special Cases

### Foreign Keys

When referencing another table's PK, use the same name:

```sql
-- dim_customers.sql
customer_id  -- Primary key

-- fct_orders.sql
customer_id  -- Foreign key (same name as dim_customers.customer_id)
```

### Calculated Metrics

Use descriptive suffixes for derived fields:

```sql
revenue_eur              -- Base metric
revenue_per_customer_eur -- Calculated metric
conversion_rate_pct      -- Percentage (0-100 scale)
```

### Temporal Grain

Include grain in column name for clarity:

```sql
dt_date           -- Daily grain
dt_week           -- Weekly grain
dt_month          -- Monthly grain
report_hour       -- Hourly grain
```

## Validation Rules

AI agents should flag these violations:

- ❌ Column named `id` without object prefix
- ❌ Timestamp without `_at` suffix
- ❌ Boolean without `is_/has_/does_` prefix
- ❌ Amount without currency code
- ❌ Model name with mixed case (e.g., `stg_PaymentMethods`)

