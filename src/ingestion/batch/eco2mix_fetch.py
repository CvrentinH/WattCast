from ingestion.batch.fetchers import BaseFetcher
import requests
import zipfile
import pandas as pd
from io import BytesIO

class Eco2Mix(BaseFetcher):

    def __init__(self, settings, year):
        super().__init__(settings)
        self.s3_key = f"raw/eco2mix/year={year}/eco2mix_national_{year}.csv"

    def fetch(self):
        for year in range(2021, 2025):
            url = f"https://eco2mix.rte-france.com/download/eco2mix/eCO2mix_RTE_Annuel-Definitif_{year}.zip"
            r = requests.get(url)
            r.raise_for_status()
            xls_stream = self._unzip(r.content)
            self.s3_body = self._xls_to_csv(xls_stream)
            self.upload_to_bronze()

    def _unzip(self, zip_bytes):
        zip_ref = zipfile.ZipFile(BytesIO(zip_bytes))
        file_zip = zip_ref.namelist()[0]
        return zip_ref.open(file_zip)

    def _xls_to_csv(self, xls_stream):
        df = pd.read_csv(xls_stream, sep="\t", encoding="latin-1", low_memory=False)
        return df.to_csv(index=False).encode("utf-8")
