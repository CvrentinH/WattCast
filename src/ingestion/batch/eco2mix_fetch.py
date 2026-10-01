from ingestion.batch.fetchers import BaseFetcher
import requests
from ingestion.batch.file_utils import unzip, xls_to_csv
from ingestion.batch.const import ECO2MIX_URL_BASE, ECO2MIX_URL_FILE, S3_KEY_TEMPLATE

class Eco2Mix(BaseFetcher):

    def __init__(self, settings, year):
        super().__init__(settings)
        self.url = ECO2MIX_URL_BASE + ECO2MIX_URL_FILE.replace("$YEAR", str(year))
        self.s3_key = S3_KEY_TEMPLATE.replace("$SOURCE","eco2mix").replace("$YEAR", str(year))

    def fetch(self):
        url = self.url
        response = requests.get(url)
        response.raise_for_status()
        xls_stream = unzip(response.content)
        self.s3_body = xls_to_csv(xls_stream)
        self.upload_to_bronze()
