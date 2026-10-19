import boto3
import redis
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker

from common.config import MinioSettings, PostgreSettings, RedisSettings
from common.exceptions import BucketInitError

# REDIS


class RedisClient:
	def __init__(self, settings: RedisSettings) -> None:
		self.settings = settings

		self.r = redis.Redis(
			host=self.settings.REDIS_HOST,
			port=self.settings.REDIS_PORT,
			password=self.settings.REDIS_PASSWORD,
			health_check_interval=60,
			db=0,
		)
		self.r.ping()


# PGSQL


class PostgreClient:
	def __init__(self, settings: PostgreSettings) -> None:
		self.settings = settings

		DB_URL = self.settings.postgres_sync_url

		self.engine = create_engine(DB_URL, echo=False, pool_size=5, max_overflow=10)
		self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False, autoflush=False)


# MINIO


class MinioClient:
	def __init__(self, settings: MinioSettings) -> None:
		self.settings = settings
		print(self.settings)
		print(settings)
		config_client = Config(
			connect_timeout=1,
			read_timeout=1,
			retries={"total_max_attempts": 1},
		)

		self.client = boto3.client(
			"s3",
			endpoint_url=self.settings.minio_url,
			aws_access_key_id=self.settings.MINIO_ROOT_USER,
			aws_secret_access_key=self.settings.MINIO_ROOT_PASSWORD,
			region_name="us-east-1",
			config=config_client,
		)
		self.init_bucket()

	def init_bucket(self) -> None:
		buckets_to_create = [
			self.settings.MINIO_BUCKET_LANDING,
			self.settings.MINIO_BUCKET_BRONZE,
			self.settings.MINIO_BUCKET_SILVER,
		]

		try:
			response = self.client.list_buckets()
		except (ClientError, BotoCoreError) as e:
			raise BucketInitError("Impossible de lister les buckets MinIO") from e

		existing_buckets = {b["Name"] for b in response.get("Buckets", [])}

		for bucket_name in buckets_to_create:
			if bucket_name not in existing_buckets:
				self.client.create_bucket(Bucket=bucket_name)
