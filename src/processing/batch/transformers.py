from abc import ABC, abstractmethod

from common.bucket_s3 import BucketS3
from common.clients import MinioClient
from common.config import Settings


class BaseTransformer(ABC):
	def __init__(self, settings: Settings, source_name: str, target_name: str) -> None:
		self.settings = settings
		client = MinioClient(settings).client
		self.source_bucket = BucketS3(client, source_name)
		self.bucket = BucketS3(client, target_name)

	@abstractmethod
	def transform(self) -> None:
		pass
