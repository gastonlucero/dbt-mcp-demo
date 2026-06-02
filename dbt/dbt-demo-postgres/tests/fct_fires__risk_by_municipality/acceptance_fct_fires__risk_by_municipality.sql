-- Acceptance test: fct_fires__risk_by_municipality
-- Returns rows only when an assertion fails. Zero rows = all good.

with model as (
    select * from {{ ref('fct_fires__risk_by_municipality') }}
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
       or total_fire_incidents is null
       or risk_level is null
    having count(*) > 0
),

-- 3. Metric sanity: counts positive, risk score within 0–1
check_metric_range as (
    select 'check_metric_range' as assertion, count(*) as failing_rows
    from model
    where total_fire_incidents < 1
       or avg_fire_risk_score < 0
       or avg_fire_risk_score > 1
       or max_fire_risk_score < 0
       or max_fire_risk_score > 1
    having count(*) > 0
),

-- 4. risk_level must only contain valid values
check_risk_level_values as (
    select 'check_risk_level_values' as assertion, count(*) as failing_rows
    from model
    where risk_level not in ('HIGH', 'MEDIUM', 'LOW')
    having count(*) > 0
),

-- 5. Grain uniqueness: one row per (country, state, municipality)
check_grain as (
    select 'check_grain_uniqueness' as assertion, count(*) as failing_rows
    from (
        select country, state, municipality, count(*) as n
        from model
        group by country, state, municipality
        having count(*) > 1
    ) dupes
    having count(*) > 0
)

select * from check_has_rows
union all select * from check_no_nulls
union all select * from check_metric_range
union all select * from check_risk_level_values
union all select * from check_grain
