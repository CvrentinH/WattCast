from abc import ABC, abstractmethod
from botocore.exceptions import ClientError

from common.clients import MinioClient
from common.config import get_settings

settings = get_settings()

class BaseFetcher(ABC):
    def __init__(self, settings):
        self.settings = settings
        self.minio_client = MinioClient(settings)
        self.bucket = self.bucket = self.settings.MINIO_BUCKET_BRONZE

        # Child time
        self.s3_key = None
        self.s3_body = None

    @abstractmethod
    def fetch(self):
        pass

    def check_bucket_init(self):
        try:
            self.minio_client.client.head_bucket(Bucket = self.bucket)
            return True
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            print(error_code)
            return False

    def upload_to_bronze(self):
        return self.minio_client.client.put_object(Bucket = self.bucket, Key = self.s3_key, Body = self.s3_body)
