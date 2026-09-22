from abc import ABC, abstractmethod

from common.clients import MinioClient
from common.config import get_settings

class BaseFetcher(ABC):
    # Abstract time
    self.settings
    self.minio_client
    self.bucket

    # Child time
    self.s3_key
    self.s3_body

    def __init__(self, settings):
        self.settings = settings
        self.minio_client = MinioClient(settings)
        self.bucket = self.settings.MINIO_BUCKET_BRONZE

    @abstractmethod
    def fetch(self):
        pass

    def upload_to_bronze(self):
        # Add check for all 3 params
        return self.minio_client.client.put_object(Bucket = self.bucket, Key = self.s3_key, Body = self.s3_body)

if __name__ == "__main__":
    settings = get_settings()
