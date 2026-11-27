from pathlib import Path

from alembic.config import Config
from alembic.util.exc import CommandError
from sqlalchemy.exc import SQLAlchemyError

from alembic import command
from common.config import PostgreSettings
from common.exceptions import DBInitError


def run_database_migrations() -> None:
    settings = PostgreSettings()

    project_root = Path(__file__).resolve().parents[2]
    alembic_ini = project_root / "alembic.ini"
    script_location = project_root / "alembic"

    if not alembic_ini.is_file():
        raise DBInitError(f"Alembic configuration not found: {alembic_ini}")

    if not script_location.is_dir():
        raise DBInitError(f"Alembic scripts directory not found: {script_location}")

    config = Config(str(alembic_ini))

    config.set_main_option(
        "script_location",
        str(script_location),
    )
    config.set_main_option(
        "sqlalchemy.url",
        settings.postgres_url.replace("%", "%%"),
    )

    try:
        command.upgrade(config, "head")
    except (SQLAlchemyError, CommandError) as error:
        raise DBInitError(f"Impossible d'appliquer les migrations PostgreSQL: {error}")
