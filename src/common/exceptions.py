class PipelineError(Exception):
	"""Base for all errors raised by the pipeline."""


class StorageError(PipelineError):
	"""Object storage (MinIO/S3) operation failed."""


class BucketInitError(StorageError):
	"""Bucket initialization failed."""


class FetchError(PipelineError):
	"""Fetching data from an external source failed."""
