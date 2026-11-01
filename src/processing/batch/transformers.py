from abc import ABC, abstractmethod

from common.bucket_s3 import BucketS3
from common.clients import get_pg_client, get_s3_client
from common.schema_pg import SchemaPG


class BaseTransformer(ABC):
    def __init__(self, source_name: str, target_name: str, schema: str) -> None:
        s3_client = get_s3_client()
        self.source_bucket = BucketS3(s3_client, source_name)
        self.target_bucket = BucketS3(s3_client, target_name)

        pg_client = get_pg_client()
        self.schema = SchemaPG(pg_client, schema)

    @abstractmethod
    def transform(self) -> None:
        pass
