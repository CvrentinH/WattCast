from abc import ABC, abstractmethod

from common.bucket_s3 import BucketS3
from common.clients import MinioClient
from common.config import Settings


class BaseFetcher(ABC):
	def __init__(self, settings: Settings) -> None:
		self.settings = settings
		client = MinioClient(settings).client
		self.bucket = BucketS3(client, settings.MINIO_BUCKET_LANDING)

	@abstractmethod
	def fetch(self) -> None:
		pass
