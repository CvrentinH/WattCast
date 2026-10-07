from pathlib import PurePosixPath

from processing.batch.file_utils import convert_to_csv, unzip
from processing.batch.transformers import BaseTransformer


class Landing_to_Bronze(BaseTransformer):
    def __init__(self, settings):
        super().__init__(settings, settings.MINIO_BUCKET_LANDING, settings.MINIO_BUCKET_BRONZE)

    def transform(self) -> None:
        for key in self.source_bucket.list_keys():
            if key.endswith("/"):
                continue

            body = self.source_bucket.read(key)

            path = PurePosixPath(key.lower())
            if path.suffix == ".zip":
                body = convert_to_csv(unzip(body))
                path = path.with_suffix(".csv")

            self.bucket.write(str(path), body)

    def ingest_into_table(self):
        """
        mettre dans la table append-only les métadonnées de la table bronze des fichiers donnés + le body en JSON
        """
