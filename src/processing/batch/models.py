from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.common.const import PG_SCHEMA_BRONZE


class Base(DeclarativeBase):
    pass


class BronzeBatch(Base):
    __tablename__ = "bronze_batch"
    __table_args__ = {"schema": PG_SCHEMA_BRONZE}

    ingestion_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    source_file: Mapped[str] = mapped_column(String, nullable=False)
    object_key: Mapped[str] = mapped_column(String, nullable=False)
