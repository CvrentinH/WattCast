from abc import abstractmethod

from common.s3_base import BaseS3Job


class BaseTransformers(BaseS3Job):
    @abstractmethod
    def transform(self):
        pass
