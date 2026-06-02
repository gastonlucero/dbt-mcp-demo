{{
    config(materialized='table')
}}
{#
  Materialization: table
  Reason: 384K source rows → ~5.5K output rows, full rebuild < 1s.
  Promote to incremental if source exceeds ~5M rows or loads become daily.
#}

-- Fact table: total fire incidents and average precipitation per country + municipality.
-- Grain: one row per (country, municipality) combination across all loaded months.

with fires as (

    select * from {{ ref('stg_fires__monthly_fires') }}

),

aggregated as (

    select
        country,
        municipality,
        state,
        country_id,
        state_id,
        municipality_id,

        -- Fire totals
        count(*)                                        as total_fire_incidents,
        count(distinct fire_event_id)                   as unique_fire_events,

        -- Precipitation averages
        round(avg(precipitation_mm), 4)                 as avg_precipitation_mm,
        round(avg(days_without_rain), 2)                as avg_days_without_rain,

        -- Fire intensity
        round(avg(fire_risk_score), 4)                  as avg_fire_risk_score,
        round(max(fire_risk_score), 4)                  as max_fire_risk_score,
        round(avg(fire_radiative_power_mw), 2)          as avg_fire_radiative_power_mw,

        -- Time window
        min(detected_at)                                as first_fire_detected_at,
        max(detected_at)                                as last_fire_detected_at

    from fires
    group by
        country,
        municipality,
        state,
        country_id,
        state_id,
        municipality_id

)

select * from aggregated
