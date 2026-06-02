{{ config(materialized='view') }}
{#
  Materialization: view
  Reason: 384K → ~5.5K rows, agregación ligera. Si crece a >1M filas fuente
  o es referenciado por 2+ marts, promover a table.
#}

-- Intermediate: Fire risk metrics aggregated by municipality.
-- Grain: One row per (country, state, municipality) combination.
-- Combines frequency, intensity, and climatic metrics with risk categorization.

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

        -- Frequency metrics
        count(distinct fire_event_id)                              as total_fire_incidents,
        round(
            count(distinct fire_event_id)::numeric /
            (extract(day from (max(detected_at) - min(detected_at))) + 1),
            2
        )                                                           as avg_incidents_per_day,

        -- Intensity metrics
        round(avg(fire_risk_score), 4)                             as avg_fire_risk_score,
        round(max(fire_risk_score), 4)                             as max_fire_risk_score,
        round(avg(fire_radiative_power_mw), 2)                     as avg_fire_radiative_power_mw,
        round(max(fire_radiative_power_mw), 2)                     as max_fire_radiative_power_mw,

        -- Climatic metrics
        round(avg(days_without_rain), 2)                           as avg_days_without_rain,
        round(avg(precipitation_mm), 4)                            as avg_precipitation_mm,

        -- Observation period
        to_char(min(detected_at), 'Month YYYY') || ' – ' ||
        to_char(max(detected_at), 'Month YYYY')                    as observation_period

    from fires
    group by country, municipality, state, country_id, state_id, municipality_id

)

-- risk_level inlined directly into aggregated to avoid an extra Subquery Scan
select
    country,
    municipality,
    state,
    country_id,
    state_id,
    municipality_id,
    total_fire_incidents,
    avg_incidents_per_day,
    avg_fire_risk_score,
    max_fire_risk_score,
    avg_fire_radiative_power_mw,
    max_fire_radiative_power_mw,
    avg_days_without_rain,
    avg_precipitation_mm,
    observation_period,
    case
        when total_fire_incidents >= 10
          and avg_fire_risk_score >= 0.6
          and avg_days_without_rain >= 10
        then 'HIGH'
        when total_fire_incidents >= 5
          and avg_fire_risk_score >= 0.4
        then 'MEDIUM'
        else 'LOW'
    end as risk_level

from aggregated
