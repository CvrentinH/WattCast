from abc import ABC, abstractmethod
from common.clients import MinioClient

class BaseFetcher(ABC):
    def __init__(self, settings):
        self.settings = settings
        self.minio_client = MinioClient(settings)
        self.bucket = self.settings.MINIO_BUCKET_BRONZE
        if not self.is_bucket_init():
            raise RuntimeError(f"{self.bucket} inaccessible ou non connecté")

        # Child time
        self.s3_key = None
        self.s3_body = None

    @abstractmethod
    def fetch(self):
        pass

    def is_bucket_init(self):
        return self.minio_client.client.head_bucket(Bucket = self.bucket) is not None

    def upload_to_bronze(self):
        if not self.s3_key or not self.s3_body:
                body_size = len(self.s3_body) if self.s3_body else 0
                raise ValueError(
                    f"Error uploading to bucket '{self.bucket}': "
                    f"s3_key={self.s3_key}, s3_body_size={body_size} bytes"
                )

        return self.minio_client.client.put_object(Bucket = self.bucket, Key = self.s3_key, Body = self.s3_body)
