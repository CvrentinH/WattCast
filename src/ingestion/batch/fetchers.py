from abc import ABC, abstractmethod

from common.clients import MinioClient
from common.config import get_settings

class BaseFetcher(ABC):
    def __init__(self, settings):
        self.settings = settings
        self.minio_client = MinioClient(settings)
        self.bucket = self.settings.MINIO_BUCKET_BRONZE

    @abstractmethod
    def fetch(self):
        pass

    def upload_to_bronze(self, s3_key, s3_body):
        return self.minio_client.client.put_object(Bucket = self.bucket, Key = s3_key, Body = s3_body)

if __name__ == "__main__":
    settings = get_settings()