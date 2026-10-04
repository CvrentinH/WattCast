ECO2MIX_URL_BASE = "https://eco2mix.rte-france.com/download/eco2mix/"
ECO2MIX_URL_FILE = "eCO2mix_RTE_Annuel-Definitif_$YEAR.zip"

OPENMETEO_URL_BASE = "https://archive-api.open-meteo.com/v1/archive"

S3_KEY_TEMPLATE = "raw/$SOURCE/year=$YEAR/$SOURCE_$YEAR.csv"

OPENMETEO_DATA_REQUEST = {
    "temperature_2m",
    "apparent_temperature",
    "wind_speed_10m",
    "cloud_cover",
    "relative_humidity_2m",
}
