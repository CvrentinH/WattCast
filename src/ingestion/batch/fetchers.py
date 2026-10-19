from abc import ABC, abstractmethod

from mypy_boto3_s3 import S3Client

from common.bucket_s3 import BucketS3
from common.clients import get_s3_client

from ingestion.batch.const import TARGET_BUCKET


class BaseFetcher(ABC):
	def __init__(self) -> None:
		self.bucket = get_s3_client()

	@abstractmethod
	def fetch(self) -> None:
		pass
