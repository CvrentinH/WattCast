from datetime import UTC, datetime
from pathlib import PurePosixPath

from common.const import MINIO_BUCKET_BRONZE, MINIO_BUCKET_LANDING, PG_SCHEMA_BRONZE
from processing.batch.file_utils import unzip, xls_to_csv
from processing.batch.models import Bronze
from processing.batch.transformers import BaseTransformer


class BronzeTransformer(BaseTransformer):
    def __init__(self) -> None:
        super().__init__(MINIO_BUCKET_LANDING, MINIO_BUCKET_BRONZE, PG_SCHEMA_BRONZE)

    def transform(self) -> list[tuple[str, str]]:

        transformed_files: list[tuple[str, str]] = []

        for key in self.source_bucket.list_keys():
            if key.endswith("/"):
                continue

            body = self.source_bucket.read(key)
            path = PurePosixPath(key.lower())
            if path.suffix not in {".csv", ".zip"}:
                raise ValueError(f"Invalid suffix type '{path.suffix}'")

            if path.suffix == ".zip":
                body = xls_to_csv(unzip(body))
                path = path.with_suffix(".csv")

            object_key = str(path)

            self.target_bucket.write(object_key, body)

            transformed_files.append((key, object_key))

        return transformed_files

    def ingest_into_table(self, transformed_files: list[tuple[str, str]]) -> None:
        if not transformed_files:
            raise ValueError("transformed_files is empty")

        ingested_at = datetime.now(UTC)
        batches: list[Bronze] = []

        for source_file, object_key in transformed_files:
            batch = Bronze(
                ingested_at=ingested_at,
                source_file=source_file,
                object_key=object_key,
            )
            batches.append(batch)

        self.schema.create_many(batches)

    def run(self) -> None:
        transformed_files = self.transform()
        self.ingest_into_table(transformed_files)
