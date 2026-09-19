import requests
from pathlib import Path
import boto3

from common.config import get_settings
from common.clients import MinioClient

class Eco2Mix:
    def __init__(self, settings):
        self.settings = settings
        self.minio_client = MinioClient(settings)
        self.bucket = self.settings.MINIO_BUCKET_BRONZE

    def fetch_eco2mix():
        BASE_DIR = Path(__file__).resolve().parents[3]
        DATA_FILE = BASE_DIR / "data" / "eco2mix" / "eCO2mix_RTE_Annuel-Definitif_2024.zip"

        if not DATA_FILE.exists():
            r= requests.get("https://eco2mix.rte-france.com/download/eco2mix/eCO2mix_RTE_Annuel-Definitif_2024.zip")
            with open(DATA_FILE, 'wb') as f:
                f.write(r.content)
