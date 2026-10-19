from abc import ABC, abstractmethod

from mypy_boto3_s3 import S3Client

from common.bucket_s3 import BucketS3
from ingestion.batch.const import TARGET_BUCKET


class BaseFetcher(ABC):
	def __init__(self, client: S3Client) -> None:
		self.bucket = BucketS3(client, TARGET_BUCKET)

	@abstractmethod
	def fetch(self) -> None:
		pass
