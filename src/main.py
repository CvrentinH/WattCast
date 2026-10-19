import logging

from common.config import MinioSettings
from common.exceptions import PipelineError
from ingestion.batch.eco2mix_fetch import Eco2Mix
from ingestion.batch.meteo_archive_fetch import OpenMeteo
from processing.batch.landing_to_bronze import BronzeTransformer

logger = logging.getLogger(__name__)


def main() -> None:
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s %(levelname)s %(name)s: %(message)s",
	)
	settings = MinioSettings()

	try:
		eco2mix = Eco2Mix(settings, year=2024)
		meteo = OpenMeteo(settings, year=2024, latitude=46, longitude=2)
		print("fetch de eco2mix")
		eco2mix.fetch()
		print(f"saved path : {eco2mix.s3_key}")
		print("eco2mix dans minio")
		print("fetch de openmeteo")
		meteo.fetch()
		print(f"saved path : {meteo.s3_key}")
		print("openmeteo dans minio")

		# Test Landing RAW to BRONZE
		landing = BronzeTransformer(settings)
		print("transform raw -> bronze")
		landing.transform()

	except PipelineError as e:
		raise PipelineError(f"Pipeline failed : {e}")


if __name__ == "__main__":
	main()
