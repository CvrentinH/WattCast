from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from common.exceptions import DBSessionError


class SchemaPG:
    def __init__(self, client: sessionmaker[Session], schema_name: str) -> None:
        if not schema_name:
            raise ValueError("Table is required")

        self.client = client
        self.schema_name = schema_name

    @contextmanager
    def session(self) -> Generator[Session]:
        db = self.client()

        try:
            yield db
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise DBSessionError(f"Erreur lors du yield de la db {e}")
        db.close()

    def create(self) -> None:
        pass

    def get_by_id(self) -> None:
        pass

    def get_all(self) -> None:
        pass

    def update(self) -> None:
        pass

    def delete(self) -> None:
        pass
