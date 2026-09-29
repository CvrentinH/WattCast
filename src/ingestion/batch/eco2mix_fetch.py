from ingestion.batch.fetchers import BaseFetcher
import requests
from ingestion.batch.file_utils import _unzip, _xls_to_csv
from ingestion.batch.const import ECO2MIX_URL_BASE, ECO2MIX_URL_FILE

class Eco2Mix(BaseFetcher):

    def __init__(self, settings, year):
        super().__init__(settings)
        self.url = ECO2MIX_URL_BASE + ECO2MIX_URL_FILE.replace("$YEAR", str(year))
        self.s3_key = self.get_s3_key(year)

    def get_s3_key(self, year):
        return f"raw/eco2mix/year={year}/eco2mix_national_{year}.csv"

    def fetch(self):
        url = self.url
        r = requests.get(url)
        r.raise_for_status()
        xls_stream = _unzip(r.content)
        self.s3_body = _xls_to_csv(xls_stream)
        self.upload_to_bronze()
