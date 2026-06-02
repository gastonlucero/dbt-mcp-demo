# Architectural Integrity (The SIM Pattern)

All models must be categorized into one of three layers. AI Agents and CI/CD checks should flag any model that violates these boundaries.

## Layer 1: Staging (`stg_`)

**Purpose:** 1:1 reflection of source tables.

**Rules:**

- Rename columns for consistency.
- Cast data types (e.g., strings to timestamps).
- Simple `CASE` are allowed.
- **Prohibited:** Joins, complex `CASE` statements, or business logic.

**Example:**

```sql
-- stg_payments.sql
SELECT
    payment_id
    , CAST(payment_date AS DATE) AS payment_date
    , payment_method
    , amount_cents
FROM {{ source('stripe', 'payments') }}
```

---

## Layer 2: Intermediate (`int_`)

**Purpose:** Reusable business logic.

**Rules:**

- Combine multiple staging models.
- Apply business filters and transformations.
- **Goal:** Create modular "bricks" used by multiple Marts.

**Example:**

```sql
-- int_customer_lifetime_value.sql
WITH customer_orders AS (
    SELECT 
     customer_id
     , SUM(amount_usd) AS total_spent
    FROM {{ ref('stg_orders') }}
    GROUP BY customer_id
)
SELECT customer_id, total_spent
FROM customer_orders
```

---

## Layer 3: Marts (`fct_`, `dim_`)

**Purpose:** Final, denormalized tables for Postgres.

**Rules:**

- `dim_`: Descriptive entities (e.g., `dim_customers`).
- `fct_`: Event-based metrics (e.g., `fct_orders`).
- Must be wide, user-friendly, and documented.

**Example:**

```sql
-- fct_daily_revenue.sql
SELECT
    date_day
    , SUM(revenue_usd) AS total_revenue
    , COUNT(DISTINCT customer_id) AS unique_customers
FROM {{ ref('int_customer_orders') }}
GROUP BY date_day
```

---

## Validation Checklist

- [ ] Model has correct prefix (`stg_`, `int_`, `fct_`, `dim_`)
- [ ] No business logic in staging layer
- [ ] Reusable business logic OR complex transformation steps broken out for readability
- [ ] Marts are fully documented with grain and use case
