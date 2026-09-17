from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../../.env", ".env"), 
                                    env_file_encoding="utf-8", 
                                    extra="ignore")

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_ENDPOINT: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET_BRONZE: str = "bucket-bronze"
    MINIO_BUCKET_SILVER: str = "bucket-silver"

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str

    KAFKA_BOOTSTRAP_SERVERS: str

    @property
    def postgresql_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def postgres_sync_url(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def minio_url(self) -> str:
        protocol = "https" if self.MINIO_SECURE else "http"
        return f"{protocol}://{self.MINIO_ENDPOINT}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
