from ingestion.batch.fetchers import BaseFetcher
import requests
from ingestion.batch.const import ECO2MIX_URL_BASE, ECO2MIX_URL_FILE, S3_KEY_TEMPLATE

class Eco2Mix(BaseFetcher):

    def __init__(self, settings, year: int):
        super().__init__(settings)
        self.url = ECO2MIX_URL_BASE + ECO2MIX_URL_FILE.replace("$YEAR", str(year))
        self.s3_key = S3_KEY_TEMPLATE.replace("$SOURCE","eco2mix").replace("$YEAR", str(year))

    def fetch(self):
        response = requests.get(self.url)
        response.raise_for_status()
        self.s3_body = response.content
        self.upload_to_landing()
