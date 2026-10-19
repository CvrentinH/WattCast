import niquests
from mypy_boto3_s3 import S3Client

from ingestion.batch.const import ECO2MIX_URL_BASE, ECO2MIX_URL_FILE, S3_KEY_TEMPLATE
from ingestion.batch.fetchers import BaseFetcher


class Eco2Mix(BaseFetcher):
	def __init__(self, client: S3Client, year: int) -> None:
		super().__init__(client)
		self.url = ECO2MIX_URL_BASE + ECO2MIX_URL_FILE.replace("$YEAR", str(year))
		self.s3_key = S3_KEY_TEMPLATE("eco2mix", str(year), "zip")

	def fetch(self) -> None:
		response = niquests.get(self.url)
		response.raise_for_status()
		content = response.content
		if content is None:
			raise ValueError(f"Content is None : {self.url}")

		self.bucket.write(self.s3_key, content)
