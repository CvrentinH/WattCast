from collections.abc import Iterator
from contextlib import closing

from botocore.exceptions import BotoCoreError, ClientError
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import PutObjectOutputTypeDef

from common.exceptions import StorageError


class BucketS3:
	def __init__(self, client: S3Client, name: str) -> None:
		if not name:
			raise ValueError("Bucket name is required")

		self.client = client
		self.name = name

	def read(self, key: str) -> bytes:
		if not key:
			raise ValueError("Object key is required")

		with closing(self.client.get_object(Bucket=self.name, Key=key)["Body"]) as stream:
			return stream.read()

	def write(self, key: str, body: bytes) -> PutObjectOutputTypeDef:
		if not key:
			raise ValueError("Object key is required")

		try:
			return self.client.put_object(Bucket=self.name, Key=key, Body=body)
		except (ClientError, BotoCoreError) as e:
			raise StorageError(f"Unable to write '{self.name}/{key}'") from e

	def list_keys(self) -> Iterator[str]:
		paginator = self.client.get_paginator("list_objects_v2")
		for page in paginator.paginate(Bucket=self.name):
			for obj in page.get("Contents", []):
				yield obj["Key"]
