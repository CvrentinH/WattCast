import logging
import sys

from common.config import get_settings
from common.exceptions import PipelineError
from ingestion.batch.eco2mix_fetch import Eco2Mix
from ingestion.batch.meteo_archive_fetch import OpenMeteo
from processing.batch.landing_to_bronze import BronzeTransformer

logger = logging.getLogger(__name__)


def main() -> int:
	logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
	settings = get_settings()

	try:
		eco2mix = Eco2Mix(settings, year=2023)
		meteo = OpenMeteo(settings, year=2023, latitude=46, longitude=2)

		logger.info("Fetching eco2mix")
		eco2mix.fetch()
		logger.info("eco2mix saved: %s", eco2mix.s3_key)

		logger.info("Fetching openmeteo")
		meteo.fetch()
		logger.info("openmeteo saved: %s", meteo.s3_key)

		logger.info("Transforming landing -> bronze")
		BronzeTransformer(settings).transform()
	except PipelineError:
		logger.exception("Pipeline failed")
		return 1

	return 0


if __name__ == "__main__":
	sys.exit(main())
