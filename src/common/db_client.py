from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from common.config import get_settings

settings = get_settings()


class PostgreClient:
    def __init__(self, settings):
        self.settings = settings
        DB_URL = self.settings.postgresql_url

        self.engine = create_engine(
            DB_URL,
            echo=False,
        )

        self.session_factory = sessionmaker(
            bind=self.engine, expire_on_commit=False, autoflush=False
        )
