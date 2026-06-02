{{ config(materialized='ephemeral') }}

-- Staging: 1-to-1 reflection of raw_data.monthly_fires with standardised column names.
-- Casts types and filters out rows with no country or municipality.

with source as (

    select * from {{ source('fires_raw', 'monthly_fires') }}

),

renamed as (

    select
        id                                          as fire_event_id,
        initcap(pais)                               as country,
        initcap(municipio)                          as municipality,
        initcap(estado)                             as state,
        pais_id                                     as country_id,
        estado_id                                   as state_id,
        municipio_id                                as municipality_id,
        cast(precipitacao as numeric)               as precipitation_mm,
        nullif(cast(risco_fogo as numeric), -999)   as fire_risk_score,
        cast(frp as numeric)                        as fire_radiative_power_mw,
        cast(numero_dias_sem_chuva as integer)      as days_without_rain,
        data_hora_gmt                               as detected_at,
        satelite                                    as satellite,
        bioma                                       as biome

    from source
    where pais is not null
      and municipio is not null

)

select * from renamed
