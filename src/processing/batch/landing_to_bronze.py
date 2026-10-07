from pathlib import PurePosixPath

from processing.batch.file_utils import convert_to_csv, unzip
from processing.batch.transformers import BaseTransformers


class Landing_to_Bronze(BaseTransformers):
    def __init__(self, settings):
        super().__init__(settings)
        self.bucket_input = self.settings.MINIO_BUCKET_LANDING
        self.bucket_output = self.settings.MINIO_BUCKET_BRONZE

    def transform(self):
        objects_list = self.minio_client.client.list_objects_v2(Bucket=self.bucket_input).get("Contents", [])
        for obj in objects_list:
            key = obj["Key"]
            if key.endswith("/"):
                continue

            self.s3_key = key
            self.fetch_from_bucket()

            path = PurePosixPath(key.lower())
            if path.suffix == ".zip":
                self.s3_body = convert_to_csv(unzip(self.s3_body))
                path = path.with_suffix(".csv")

            self.s3_key = str(path)
            self.upload_to_bucket()

    def ingest_into_table(self):
        """
        mettre dans la table append-only les métadonnées de la table bronze des fichiers donnés + le body en JSON
        """
