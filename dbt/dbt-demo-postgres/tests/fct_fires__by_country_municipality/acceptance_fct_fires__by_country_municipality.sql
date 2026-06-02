-- Acceptance test: fct_fires__by_country_municipality
-- Returns rows only when an assertion fails. Zero rows = all good.

with model as (
    select * from {{ ref('fct_fires__by_country_municipality') }}
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
    having count(*) > 0
),

-- 3. Fire counts must be positive
check_metric_range as (
    select 'check_metric_range' as assertion, count(*) as failing_rows
    from model
    where total_fire_incidents < 1
       or unique_fire_events < 1
    having count(*) > 0
),

-- 4. Grain uniqueness: one row per (country, state, municipality)
-- Note: same municipality name can exist in different states (e.g. "São Vicente" in SP and SC)
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
union all select * from check_grain
