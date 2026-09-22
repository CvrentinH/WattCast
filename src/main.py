from common.config import get_settings
from ingestion.batch.eco2mix_fetch import Eco2Mix
from ingestion.batch.meteo_archive_fetch import OpenMeteo


def main():
    settings = get_settings()
    eco2mix = Eco2Mix(settings, year=2021)
    meteo = OpenMeteo(settings, year=2021)

    eco2mix.fetch()
    meteo.fetch()

if __name__ == "__main__":
    main()
