from common.config import get_settings
from ingestion.batch.eco2mix_fetch import Eco2Mix
from ingestion.batch.meteo_archive_fetch import OpenMeteo


def main():
    settings = get_settings()
    eco2mix = Eco2Mix(settings, year=2021)
    meteo = OpenMeteo(settings, year=2021)

    print("fetch de eco2mix")
    eco2mix.fetch()
    print("eco2mix dans minio")
    print("fetch de openmeteo")
    meteo.fetch()
    print("openmeteo dans minio")

if __name__ == "__main__":
    main()
