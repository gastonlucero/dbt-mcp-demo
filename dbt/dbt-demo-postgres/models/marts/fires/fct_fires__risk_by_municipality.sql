{{
    config(materialized='table')
}}
{#
  Materialization: table
  Reason: mart final para BI/reporting. int_ ya agrega los 384K→5.5K,
  esta tabla es un SELECT simple del int_. Promote to incremental si el int_
  supera 5M filas fuente o pasa a carga diaria.
#}

-- Fact table: fire risk analysis by municipality.
-- Grain: One row per (country, state, municipality) combination.
-- Materialized denormalized table for reporting.

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
    risk_level
from {{ ref('int_fires__risk_by_municipality') }}
