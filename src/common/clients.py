import boto3

# import redis
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from mypy_boto3_s3 import S3Client
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema

from common.config import MinioSettings, PostgreSettings

# RedisSettings
from common.const import (
    MINIO_BUCKET_BRONZE,
    MINIO_BUCKET_LANDING,
    MINIO_BUCKET_SILVER,
    PG_SCHEMA_BRONZE,
    PG_SCHEMA_SILVER,
)
from common.exceptions import BucketInitError, DBInitError

# REDIS


"""
class RedisClient:
	def __init__(self, settings: RedisSettings) -> None:
		settings = settings

		r = redis.Redis(
			host=settings.REDIS_HOST,
			port=settings.REDIS_PORT,
			password=settings.REDIS_PASSWORD,
			health_check_interval=60,
			db=0,
		)
		r.ping()
"""


# PGSQL


def get_pg_client() -> sessionmaker[Session]:
    settings = PostgreSettings()

    DB_URL = settings.postgres_sync_url
    engine = create_engine(DB_URL, echo=False, pool_size=5, max_overflow=10)

    schemas_to_create = [
        PG_SCHEMA_BRONZE,
        PG_SCHEMA_SILVER,
    ]

    try:
        with engine.begin() as conn:
            for schema in schemas_to_create:
                conn.execute(CreateSchema(schema, if_not_exists=True))
    except SQLAlchemyError as e:
        engine.dispose()
        raise DBInitError("Impossible de se connecter à PostgreSQL") from e

    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


# MINIO


def get_s3_client() -> S3Client:
    settings = MinioSettings()
    config_client = Config(
        connect_timeout=1,
        read_timeout=1,
        retries={"total_max_attempts": 1},
    )

    client = boto3.client(
        "s3",
        endpoint_url=settings.minio_url,
        aws_access_key_id=settings.MINIO_ROOT_USER,
        aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        region_name="us-east-1",
        config=config_client,
    )

    buckets_to_create = [
        MINIO_BUCKET_LANDING,
        MINIO_BUCKET_BRONZE,
        MINIO_BUCKET_SILVER,
    ]

    try:
        response = client.list_buckets()
    except (ClientError, BotoCoreError) as e:
        raise BucketInitError("Impossible de lister les buckets MinIO") from e

    existing_buckets = {b["Name"] for b in response.get("Buckets", [])}

    for bucket_name in buckets_to_create:
        if bucket_name not in existing_buckets:
            client.create_bucket(Bucket=bucket_name)

    return client
