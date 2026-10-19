ECO2MIX_URL_BASE = "https://eco2mix.rte-france.com/download/eco2mix/"
ECO2MIX_URL_FILE = "eCO2mix_RTE_Annuel-Definitif_$YEAR.zip"

OPENMETEO_URL_BASE = "https://archive-api.open-meteo.com/v1/archive"

S3_KEY_TEMPLATE = lambda source, year, ext: f"{source}/year={year}/{source}_{year}.{ext}"

OPENMETEO_DATA_REQUEST = (
	"temperature_2m",
	"apparent_temperature",
	"wind_speed_10m",
	"cloud_cover",
	"relative_humidity_2m",
)

OPENMETEO_MAX_RETRIES = 5
OPENMETEO_BACKOFF_FACTOR = 0.2
