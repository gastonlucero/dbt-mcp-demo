CREATE SCHEMA IF NOT EXISTS raw_data;

-- Fires May (existing table)
CREATE TABLE IF NOT EXISTS raw_data.monthly_fires (
    id                    UUID PRIMARY KEY,
    lat                   double precision NOT NULL,
    lon                   double precision NOT NULL,
    data_hora_gmt         TIMESTAMP NOT NULL,
    satelite              VARCHAR(50),
    municipio             VARCHAR(255),
    estado                VARCHAR(255),
    pais                  VARCHAR(100),
    municipio_id          INTEGER,
    estado_id             INTEGER,
    pais_id               INTEGER,
    numero_dias_sem_chuva INTEGER,
    precipitacao          NUMERIC(8,2),
    risco_fogo            NUMERIC(8,4),
    bioma                 VARCHAR(100),
    frp                   NUMERIC(8,2)
);

COPY raw_data.monthly_fires (id, lat, lon, data_hora_gmt, satelite, municipio, estado, pais, municipio_id, estado_id, pais_id, numero_dias_sem_chuva, precipitacao, risco_fogo, bioma, frp)
FROM '/docker-entrypoint-initdb.d/fires_202604.csv'
WITH (FORMAT csv, HEADER true, NULL '');

COPY raw_data.monthly_fires (id, lat, lon, data_hora_gmt, satelite, municipio, estado, pais, municipio_id, estado_id, pais_id, numero_dias_sem_chuva, precipitacao, risco_fogo, bioma, frp)
FROM '/docker-entrypoint-initdb.d/fires_202605.csv'
WITH (FORMAT csv, HEADER true, NULL '');

-- Temporary tables for loading CSV data
CREATE TEMP TABLE temp_argentina (
    ano INTEGER,
    janeiro INTEGER,
    fevereiro INTEGER,
    marco INTEGER,
    abril INTEGER,
    maio INTEGER,
    junho INTEGER,
    julho INTEGER,
    agosto INTEGER,
    setembro INTEGER,
    outubro INTEGER,
    novembro INTEGER,
    dezembro INTEGER,
    total INTEGER
);

CREATE TEMP TABLE temp_brasil (
    ano INTEGER,
    janeiro INTEGER,
    fevereiro INTEGER,
    marco INTEGER,
    abril INTEGER,
    maio INTEGER,
    junho INTEGER,
    julho INTEGER,
    agosto INTEGER,
    setembro INTEGER,
    outubro INTEGER,
    novembro INTEGER,
    dezembro INTEGER,
    total INTEGER
);

-- Load Argentina fires into temp table
COPY temp_argentina (ano, janeiro, fevereiro, marco, abril, maio, junho, julho, agosto, setembro, outubro, novembro, dezembro, total)
FROM '/docker-entrypoint-initdb.d/history_fires_argentina.csv'
WITH (FORMAT csv, HEADER true, NULL '');

-- Load Brasil fires into temp table
COPY temp_brasil (ano, janeiro, fevereiro, marco, abril, maio, junho, julho, agosto, setembro, outubro, novembro, dezembro, total)
FROM '/docker-entrypoint-initdb.d/history_fires_brasil.csv'
WITH (FORMAT csv, HEADER true, NULL '');

-- Historical fires by country (Argentina & Brasil in same table)
CREATE TABLE IF NOT EXISTS raw_data.history_fires_regional (
    pais VARCHAR(50) NOT NULL,
    ano INTEGER NOT NULL,
    janeiro INTEGER,
    fevereiro INTEGER,
    marco INTEGER,
    abril INTEGER,
    maio INTEGER,
    junho INTEGER,
    julho INTEGER,
    agosto INTEGER,
    setembro INTEGER,
    outubro INTEGER,
    novembro INTEGER,
    dezembro INTEGER,
    total INTEGER,
    PRIMARY KEY (pais, ano)
);

-- Insert Argentina data with pais column
INSERT INTO raw_data.history_fires_regional (pais, ano, janeiro, fevereiro, marco, abril, maio, junho, julho, agosto, setembro, outubro, novembro, dezembro, total)
SELECT 'Argentina', ano, janeiro, fevereiro, marco, abril, maio, junho, julho, agosto, setembro, outubro, novembro, dezembro, total
FROM temp_argentina;

-- Insert Brasil data with pais column
INSERT INTO raw_data.history_fires_regional (pais, ano, janeiro, fevereiro, marco, abril, maio, junho, julho, agosto, setembro, outubro, novembro, dezembro, total)
SELECT 'Brasil', ano, janeiro, fevereiro, marco, abril, maio, junho, julho, agosto, setembro, outubro, novembro, dezembro, total
FROM temp_brasil;

-- Historical fires LATAM
CREATE TABLE IF NOT EXISTS raw_data.history_fires_latam (
    ano INTEGER PRIMARY KEY,
    janeiro INTEGER,
    fevereiro INTEGER,
    marco INTEGER,
    abril INTEGER,
    maio INTEGER,
    junho INTEGER,
    julho INTEGER,
    agosto INTEGER,
    setembro INTEGER,
    outubro INTEGER,
    novembro INTEGER,
    dezembro INTEGER,
    total INTEGER
);

COPY raw_data.history_fires_latam (ano, janeiro, fevereiro, marco, abril, maio, junho, julho, agosto, setembro, outubro, novembro, dezembro, total)
FROM '/docker-entrypoint-initdb.d/history_fires_latam.csv'
WITH (FORMAT csv, HEADER true, NULL '');