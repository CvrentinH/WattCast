from abc import ABC, abstractmethod

from common.bucket_s3 import BucketS3
from common.clients import get_s3_client
from ingestion.batch.const import TARGET_BUCKET


class BaseFetcher(ABC):
	def __init__(self) -> None:
		self.bucket = BucketS3(get_s3_client(), TARGET_BUCKET)

	@abstractmethod
	def fetch(self) -> None:
		pass
