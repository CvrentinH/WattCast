from abc import ABC, abstractmethod

from common.bucket_s3 import BucketS3
from common.clients import get_s3_client


class BaseTransformer(ABC):
	def __init__(self, source_name: str, target_name: str) -> None:
		client = get_s3_client()
		self.source_bucket = BucketS3(client, source_name)
		self.target_bucket = BucketS3(client, target_name)

	@abstractmethod
	def transform(self) -> None:
		pass
