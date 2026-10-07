from abc import abstractmethod

from common.s3_base import BaseS3Job


class BaseFetcher(BaseS3Job):
    def __init__(self, settings):
        super().__init__(settings)
        self.bucket_output = self.settings.MINIO_BUCKET_LANDING

    @property
    def bucket(self):
        return self.bucket_output

    @abstractmethod
    def fetch(self):
        pass
