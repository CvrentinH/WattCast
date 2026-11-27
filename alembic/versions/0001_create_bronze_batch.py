from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_create_bronze_batch"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS bronze")

    op.create_table(
        "bronze_batch",
        sa.Column(
            "ingestion_id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "source_file",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "object_key",
            sa.String(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("ingestion_id"),
        schema="bronze",
    )


def downgrade() -> None:
    op.drop_table("bronze_batch", schema="bronze")
    op.execute("DROP SCHEMA IF EXISTS bronze")
