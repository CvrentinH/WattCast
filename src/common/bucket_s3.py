from collections.abc import Iterator
from contextlib import closing
from typing import Any

from botocore.client import BaseClient


class BucketS3:
	def __init__(self, client: BaseClient, name: str) -> None:
		if not name:
			raise ValueError("Bucket name is required")

		self.client = client
		self.name = name

	def read(self, key: str) -> bytes:
		if not key:
			raise ValueError("Object key is required")

		with closing(self.client.get_object(Bucket=self.name, Key=key)["Body"]) as stream:
			return stream.read()

	def write(self, key: str, body: bytes) -> dict[str, Any]:
		if not key:
			raise ValueError("Object key is required")

		if body is None:
			raise ValueError("Object body is required")

		return self.client.put_object(Bucket=self.name, Key=key, Body=body)

	def list_keys(self) -> Iterator[str]:
		paginator = self.client.get_paginator("list_objects_v2")
		for page in paginator.paginate(Bucket=self.name):
			for obj in page.get("Contents", []):
				yield obj["Key"]
