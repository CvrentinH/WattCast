from abc import ABC

from common.clients import MinioClient


class BaseS3Job(ABC):
    def __init__(self, settings):
        self.settings = settings
        self.minio_client = MinioClient(settings)
        self.s3_key = None
        self.s3_body = None
        self.bucket_input = None
        self.bucket_output = None

    def fetch_from_bucket(self, bucket=None, key=None):
        target_bucket = bucket or self.bucket_input
        key = self.s3_key
        if not target_bucket or not key:
            raise ValueError(f"'bucket' and 'key' are required (bucket={target_bucket}, key={key})")
        self.s3_body = self.minio_client.client.get_object(Bucket=target_bucket, Key=key)["Body"].read()
        return self.s3_body

    def upload_to_bucket(self, bucket=None, key=None, body=None):
        target_bucket = bucket or self.bucket_output
        target_key = key or self.s3_key
        payload = body if body is not None else self.s3_body
        if not target_bucket or not target_key:
            raise ValueError(f"'bucket' and 'key' are required (bucket={target_bucket}, key={target_key})")
        if payload is None:
            raise ValueError(f"Body is empty for bucket '{target_bucket}' and key '{target_key}'")
        return self.minio_client.client.put_object(
            Bucket=target_bucket, Key=target_key, Body=payload
        )
