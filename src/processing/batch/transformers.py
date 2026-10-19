from abc import ABC, abstractmethod

from common.bucket_s3 import BucketS3
from common.clients import MinioClient
from common.config import MinioSettings


class BaseTransformer(ABC):
	def __init__(self, settings: MinioSettings, source_name: str, target_name: str) -> None:
		client = MinioClient(settings).client
		self.source_bucket = BucketS3(client, source_name)
		self.target_bucket = BucketS3(client, target_name)

	@abstractmethod
	def transform(self) -> None:
		pass
