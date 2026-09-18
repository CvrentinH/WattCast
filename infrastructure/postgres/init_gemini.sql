-- =============================================================================
-- WattCast - Schéma Initial PostgreSQL (Gold & Serving Layer)
-- Version : 1.0 (Sprint 1.2 & Dossier d'Architecture Technique DAT)
-- Fichier : infrastructure/postgres/init_gemini.sql
-- =============================================================================

-- Extensions utiles pour les séries temporelles et calculs géographiques légers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 1. TABLE DE DIMENSION : Référentiel des Nœuds Électriques (dim_grid_node)
-- =============================================================================
-- Représente la topologie du réseau de transport et de distribution (niveaux national,
-- régional ou sous-stations/postes sources).
CREATE TABLE IF NOT EXISTS dim_grid_node (
    node_id              VARCHAR(50) PRIMARY KEY,              -- Ex: 'FR_NATIONAL', 'NODE_IDF_01', 'RTE_AURA'
    node_name            VARCHAR(100) NOT NULL,                -- Nom d'usage (ex: 'Île-de-France Poste 01')
    region_code          VARCHAR(10),                          -- Code INSEE région (ex: '11', '84')
    region_name          VARCHAR(100) NOT NULL,                -- Nom de région (ex: 'Île-de-France')
    department_code      VARCHAR(5),                           -- Code département éventuel (ex: '75', '69')
    latitude             NUMERIC(9, 6) NOT NULL,               -- Coordonnées GPS pour mapping Open-Meteo & Power BI
    longitude            NUMERIC(9, 6) NOT NULL,
    max_capacity_mw      DOUBLE PRECISION NOT NULL,            -- Capacité maximale admissible en MW (seuil de surcharge)
    voltage_nominal_kv   DOUBLE PRECISION DEFAULT 400.0,       -- Tension nominale en kV (400 kV, 225 kV, 63 kV, etc.)
    node_type            VARCHAR(30) DEFAULT 'REGIONAL_SUBSTATION', -- 'NATIONAL', 'REGIONAL', 'SUBSTATION', 'SMART_METER'
    is_active            BOOLEAN DEFAULT TRUE,
    created_at           TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE dim_grid_node IS 'Référentiel des nœuds et sous-stations électriques du réseau';
COMMENT ON COLUMN dim_grid_node.max_capacity_mw IS 'Capacité maximale en MW avant risque de saturation du réseau';

-- =============================================================================
-- 2. TABLE DE FAITS : Consommation & Météo Horaire (fact_power_consumption_hourly)
-- =============================================================================
-- Couche Gold consolidée par Apache Spark (Sprint 2.2).
-- Réconcilie la consommation réelle eCO2mix, les prévisions de référence RTE et la météo Open-Meteo.
CREATE TABLE IF NOT EXISTS fact_power_consumption_hourly (
    id                           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    timestamp                    TIMESTAMPTZ NOT NULL,         -- Horodatage normalisé UTC (début de l'heure)
    node_id                      VARCHAR(50) NOT NULL REFERENCES dim_grid_node(node_id) ON DELETE CASCADE,

    -- Consommation électrique (eCO2mix RTE)
    consumption_actual_mw        DOUBLE PRECISION NOT NULL,    -- Consommation réelle mesurée (MW)
    rte_forecast_d1_mw           DOUBLE PRECISION,             -- Prévision officielle RTE J-1 (D-1) pour benchmark
    rte_forecast_d0_mw           DOUBLE PRECISION,             -- Prévision officielle RTE intra-journalière (D)

    -- Variables Météo Exogènes (Open-Meteo Historical / Forecast)
    temperature_2m_c             REAL,                         -- Température à 2 mètres (°C)
    apparent_temperature_c      REAL,                         -- Température ressentie (°C, impact thermosensibilité)
    relative_humidity_pct        REAL,                         -- Humidité relative (%)
    wind_speed_10m_kmh           REAL,                         -- Vitesse du vent à 10m (km/h)
    wind_gusts_10m_kmh           REAL,                         -- Rafales de vent (km/h)
    direct_normal_irradiance_wm2 REAL,                         -- Ensoleillement direct (W/m², corrélé au solaire)
    cloud_cover_pct              REAL,                         -- Nébulosité (%)
    precipitation_mm             REAL,                         -- Précipitations (mm)

    -- Features Calendaires (calculées par le job Spark Bronze -> Gold)
    hour_of_day                  SMALLINT CHECK (hour_of_day BETWEEN 0 AND 23),
    day_of_week                  SMALLINT CHECK (day_of_week BETWEEN 1 AND 7),  -- 1=Lundi, 7=Dimanche
    month                        SMALLINT CHECK (month BETWEEN 1 AND 12),
    is_weekend                   BOOLEAN DEFAULT FALSE,
    is_holiday                   BOOLEAN DEFAULT FALSE,

    -- Mix de Production par filière (MW) - Optionnel mais disponible dans eCO2mix
    nuclear_mw                   DOUBLE PRECISION,
    wind_mw                      DOUBLE PRECISION,
    solar_mw                     DOUBLE PRECISION,
    hydro_mw                     DOUBLE PRECISION,
    gas_mw                       DOUBLE PRECISION,
    bioenergy_mw                 DOUBLE PRECISION,
    co2_rate_g_kwh               REAL,                         -- Émissions CO2 en g/kWh

    created_at                   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Contrainte d'unicité temporelle par nœud : empêche les doublons lors des ré-exécutions Spark
    CONSTRAINT uq_consumption_node_time UNIQUE (timestamp, node_id)
);

COMMENT ON TABLE fact_power_consumption_hourly IS 'Données historiques consolidées Gold : consommation, météo et mix énergétique';

-- Index d'accélération pour requêtes chronologiques et Power BI
CREATE INDEX IF NOT EXISTS idx_power_consumption_time_node 
    ON fact_power_consumption_hourly (timestamp DESC, node_id);

CREATE INDEX IF NOT EXISTS idx_power_consumption_node_time 
    ON fact_power_consumption_hourly (node_id, timestamp DESC);

-- =============================================================================
-- 3. TABLE DE FAITS : Logs des Prédictions du Modèle (fact_predictions)
-- =============================================================================
-- Enregistre chaque inférence réalisée par l'API FastAPI (Sprint 6.1 & 6.2).
-- Permet la comparaison prédiction vs réalité pour déclencher le réentraînement (Sprint 5.3).
CREATE TABLE IF NOT EXISTS fact_predictions (
    id                           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    prediction_timestamp         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Heure où la prédiction a été faite
    target_timestamp             TIMESTAMPTZ NOT NULL,                           -- Heure cible prédite (ex: J+1 à 14h00)
    node_id                      VARCHAR(50) NOT NULL REFERENCES dim_grid_node(node_id) ON DELETE CASCADE,
    predicted_consumption_mw     DOUBLE PRECISION NOT NULL,                      -- Charge prédite par le modèle (MW)
    model_version                VARCHAR(50) NOT NULL,                           -- Ex: 'xgb_v1.0.0', 'lgbm_v2.1.0'
    inference_mode               VARCHAR(30) NOT NULL DEFAULT 'NORMAL',          -- 'NORMAL', 'CIRCUIT_BREAKER_FALLBACK_J7', 'HEURISTIC'
    latency_ms                   REAL,                                           -- Temps d'exécution de l'inférence en ms
    features_payload             JSONB,                                          -- Snapshot optionnel du vecteur d'entrée
    created_at                   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Une seule prédiction active par version de modèle, date cible et nœud
    CONSTRAINT uq_prediction_target_node_version UNIQUE (target_timestamp, node_id, model_version)
);

COMMENT ON TABLE fact_predictions IS 'Historique des inférences du modèle ML et suivi du Circuit Breaker';

CREATE INDEX IF NOT EXISTS idx_predictions_target_node 
    ON fact_predictions (target_timestamp DESC, node_id);

CREATE INDEX IF NOT EXISTS idx_predictions_model_version 
    ON fact_predictions (model_version);

-- =============================================================================
-- 4. TABLE DE SUIVI : Métriques MLOps & Détection de Dérive (model_metrics_history)
-- =============================================================================
-- Alimentée par le DAG Airflow de monitoring (Sprint 5.3) pour calculer le MAPE/RMSE
-- de la semaine écoulée et piloter le réentraînement si MAPE > 5%.
CREATE TABLE IF NOT EXISTS model_metrics_history (
    id                           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    evaluation_date              DATE NOT NULL,                                  -- Date du calcul de la métrique
    period_start                 TIMESTAMPTZ NOT NULL,                           -- Début de la fenêtre évaluée
    period_end                   TIMESTAMPTZ NOT NULL,                           -- Fin de la fenêtre évaluée
    node_id                      VARCHAR(50) NOT NULL REFERENCES dim_grid_node(node_id) ON DELETE CASCADE,
    model_version                VARCHAR(50) NOT NULL,
    sample_count                 INTEGER NOT NULL,                               -- Nombre d'heures comparées
    mape                         NUMERIC(6, 3) NOT NULL,                         -- Mean Absolute Percentage Error (%)
    rmse                         DOUBLE PRECISION NOT NULL,                      -- Root Mean Squared Error (MW)
    mae                          DOUBLE PRECISION NOT NULL,                      -- Mean Absolute Error (MW)
    is_drift_detected            BOOLEAN DEFAULT FALSE,                          -- TRUE si MAPE > seuil (ex: 5%)
    retraining_triggered         BOOLEAN DEFAULT FALSE,                          -- TRUE si Airflow a lancé un réentraînement
    created_at                   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_model_metrics_eval UNIQUE (evaluation_date, node_id, model_version)
);

COMMENT ON TABLE model_metrics_history IS 'Historique du suivi de la performance des modèles et détection de dérive (MLOps)';

CREATE INDEX IF NOT EXISTS idx_metrics_date_node 
    ON model_metrics_history (evaluation_date DESC, node_id);

-- =============================================================================
-- 5. COUCHE TEMPS RÉEL (SPEED LAYER) : Agrégats 5 minutes Flink (fact_telemetry_5min)
-- =============================================================================
-- Réf: DAT Section 2.B / 2.C et Sprint 4.2.
-- Flink calcule des tumbling windows de 5 min depuis Kafka et insère dans PostgreSQL
-- pour alimenter l'historique chaud et les dashboards Grafana/Power BI.
CREATE TABLE IF NOT EXISTS fact_telemetry_5min (
    id                           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    window_start                 TIMESTAMPTZ NOT NULL,
    window_end                   TIMESTAMPTZ NOT NULL,
    node_id                      VARCHAR(50) NOT NULL REFERENCES dim_grid_node(node_id) ON DELETE CASCADE,
    avg_active_power_mw          DOUBLE PRECISION NOT NULL,
    min_active_power_mw          DOUBLE PRECISION NOT NULL,
    max_active_power_mw          DOUBLE PRECISION NOT NULL,
    avg_voltage_kv               REAL,                                           -- Tension moyenne mesurée (kV)
    avg_frequency_hz             REAL,                                           -- Fréquence réseau (Hz, ref: 50.0 Hz)
    sample_count                 INTEGER NOT NULL,
    created_at                   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_telemetry_5min UNIQUE (window_start, node_id)
);

COMMENT ON TABLE fact_telemetry_5min IS 'Agrégats haute fréquence (5 min) générés par Apache Flink';

CREATE INDEX IF NOT EXISTS idx_telemetry_window_node 
    ON fact_telemetry_5min (window_start DESC, node_id);

-- =============================================================================
-- 6. COUCHE ALERTES TEMPS RÉEL : Détection d'anomalies (fact_grid_alerts)
-- =============================================================================
-- Enregistre les alertes instantanées détectées par Flink (surtension, sous-fréquence,
-- dépassement de capacité max_capacity_mw).
CREATE TABLE IF NOT EXISTS fact_grid_alerts (
    id                           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    alert_timestamp              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    node_id                      VARCHAR(50) NOT NULL REFERENCES dim_grid_node(node_id) ON DELETE CASCADE,
    alert_type                   VARCHAR(50) NOT NULL,                           -- 'OVERVOLTAGE', 'FREQUENCY_DEVIATION', 'CAPACITY_OVERLOAD'
    severity                     VARCHAR(20) NOT NULL CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),
    metric_value                 DOUBLE PRECISION NOT NULL,                      -- Valeur observée (ex: 50.25 Hz ou 1520 MW)
    threshold_value              DOUBLE PRECISION NOT NULL,                      -- Seuil dépassé
    description                  TEXT,
    is_acknowledged              BOOLEAN DEFAULT FALSE,
    created_at                   TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE fact_grid_alerts IS 'Alertes et anomalies réseau en temps réel générées par la Speed Layer';

CREATE INDEX IF NOT EXISTS idx_alerts_timestamp_severity 
    ON fact_grid_alerts (alert_timestamp DESC, severity);

-- =============================================================================
-- 7. VUES ANALYTIQUES POUR POWER BI & DASHBOARDS (Sprint 7)
-- =============================================================================

-- Vue comparative : Consommation réelle vs Prédiction du Modèle vs Prévision RTE
CREATE OR REPLACE VIEW vw_power_bi_consumption_vs_prediction AS
SELECT 
    f.timestamp,
    f.node_id,
    n.region_name,
    n.max_capacity_mw,
    f.consumption_actual_mw,
    f.rte_forecast_d1_mw,
    p.predicted_consumption_mw,
    p.model_version,
    p.inference_mode,
    (p.predicted_consumption_mw - f.consumption_actual_mw) AS error_mw,
    ROUND(
        (ABS(p.predicted_consumption_mw - f.consumption_actual_mw) / NULLIF(f.consumption_actual_mw, 0) * 100)::numeric, 
        2
    ) AS error_pct,
    f.temperature_2m_c,
    f.wind_speed_10m_kmh,
    f.is_weekend,
    f.is_holiday
FROM fact_power_consumption_hourly f
JOIN dim_grid_node n ON f.node_id = n.node_id
LEFT JOIN fact_predictions p 
    ON f.timestamp = p.target_timestamp 
   AND f.node_id = p.node_id;

COMMENT ON VIEW vw_power_bi_consumption_vs_prediction IS 'Vue Power BI : benchmark temps réel entre réalité, prédiction WattCast et prévision RTE';

-- Vue de synthèse de santé des nœuds (taux de charge actuel par rapport à la capacité max)
CREATE OR REPLACE VIEW vw_grid_node_status AS
SELECT 
    n.node_id,
    n.node_name,
    n.region_name,
    n.latitude,
    n.longitude,
    n.max_capacity_mw,
    t.avg_active_power_mw AS current_load_mw,
    ROUND(((t.avg_active_power_mw / NULLIF(n.max_capacity_mw, 0)) * 100)::numeric, 2) AS load_rate_pct,
    CASE 
        WHEN (t.avg_active_power_mw / NULLIF(n.max_capacity_mw, 0)) >= 0.90 THEN 'CRITICAL'
        WHEN (t.avg_active_power_mw / NULLIF(n.max_capacity_mw, 0)) >= 0.75 THEN 'WARNING'
        ELSE 'NORMAL'
    END AS grid_status,
    t.window_end AS last_measurement_time
FROM dim_grid_node n
LEFT JOIN LATERAL (
    SELECT avg_active_power_mw, window_end
    FROM fact_telemetry_5min
    WHERE node_id = n.node_id
    ORDER BY window_start DESC
    LIMIT 1
) t ON TRUE;

COMMENT ON VIEW vw_grid_node_status IS 'Statut en direct de la charge des nœuds pour la carte géographique Power BI';

-- =============================================================================
-- 8. DONNÉES DE RÉFÉRENCE INITIALES (SEED DATA)
-- =============================================================================
-- Initialisation des nœuds clés de France (National + Régions administratives principales)
INSERT INTO dim_grid_node (node_id, node_name, region_code, region_name, latitude, longitude, max_capacity_mw, node_type)
VALUES
    ('FR_NATIONAL', 'Réseau National France', '00', 'France Entière', 46.603354, 1.888334, 110000.0, 'NATIONAL'),
    ('NODE_IDF_01', 'Poste Source Paris-Nord', '11', 'Île-de-France', 48.856614, 2.352222, 14500.0, 'REGIONAL_SUBSTATION'),
    ('NODE_AURA_01', 'Poste Source Lyon-Est', '84', 'Auvergne-Rhône-Alpes', 45.764043, 4.835659, 11500.0, 'REGIONAL_SUBSTATION'),
    ('NODE_PACA_01', 'Poste Source Marseille-Littoral', '93', 'Provence-Alpes-Côte d''Azur', 43.296482, 5.369780, 8500.0, 'REGIONAL_SUBSTATION'),
    ('NODE_NAQ_01', 'Poste Source Bordeaux-Mérignac', '75', 'Nouvelle-Aquitaine', 44.837789, -0.579180, 7800.0, 'REGIONAL_SUBSTATION'),
    ('NODE_OCC_01', 'Poste Source Toulouse-Sud', '76', 'Occitanie', 43.604652, 1.444209, 7200.0, 'REGIONAL_SUBSTATION'),
    ('NODE_HDF_01', 'Poste Source Lille-Flandres', '32', 'Hauts-de-France', 50.629250, 3.057256, 8900.0, 'REGIONAL_SUBSTATION'),
    ('NODE_GES_01', 'Poste Source Strasbourg-Rhin', '44', 'Grand Est', 48.573405, 7.752111, 7900.0, 'REGIONAL_SUBSTATION')
ON CONFLICT (node_id) DO NOTHING;
