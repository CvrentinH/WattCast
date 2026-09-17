import os
import tempfile
import boto3
import polars as pl

from common.config import get_settings

settings = get_settings()


class MinioClient:
    def __init__(self, settings):
        self.settings = settings

        self.client = boto3.client(
            "s3",
            endpoint_url=self.settings.minio_url,
            aws_access_key_id=self.settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=self.settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
        )

    def upload_df(self, df: pl.DataFrame, bucket_name: str, object_name: str) -> str:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            if object_name.endswith(".csv"):
                df.write_csv(tmp_path)
            elif object_name.endswith(".json"):
                df.write_json(tmp_path)
            else:
                df.write_parquet(tmp_path)

            self.client.upload_file(tmp_path, bucket_name, object_name)
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=1800,  # 30 minutes
        )
