from common.clients import MinioClient
from common.config import get_settings

class Bronze_to_Silver():
    def __init__(self, settings):
        self.settings = settings
        self.minio_client = MinioClient(settings)
        self.bucket = self.settings.MINIO_BUCKET_BRONZE

    def retrieve_files(self):
        try:
            self.minio_client.client.get_object(
                Bucket=self.bucket
            )