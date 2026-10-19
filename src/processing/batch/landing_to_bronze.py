from pathlib import PurePosixPath

from common.config import MinioSettings
from processing.batch.file_utils import unzip, xls_to_csv
from processing.batch.transformers import BaseTransformer


class BronzeTransformer(BaseTransformer):
	def __init__(self, settings: MinioSettings) -> None:
		super().__init__(settings, settings.MINIO_BUCKET_LANDING, settings.MINIO_BUCKET_BRONZE)

	def transform(self) -> None:
		for key in self.source_bucket.list_keys():
			if key.endswith("/"):
				continue

			body = self.source_bucket.read(key)
			path = PurePosixPath(key.lower())
			if path.suffix != ".csv" and path.suffix != ".zip":
				raise ValueError(f"Invalid suffix type '{path.suffix}'")

			if path.suffix == ".zip":
				body = xls_to_csv(unzip(body))
				path = path.with_suffix(".csv")

			self.target_bucket.write(str(path), body)

	def ingest_into_table(self) -> None:
		"""
		mettre dans la table append-only les métadonnées de la table bronze des fichiers donnés + le body en JSON
		"""
