from collections.abc import Generator, Iterable
from contextlib import contextmanager
from typing import TypeVar

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from common.exceptions import DBSessionError

ModelT = TypeVar("ModelT", bound=DeclarativeBase)


class SchemaPG:
    def __init__(self, client: sessionmaker[Session], schema_name: str) -> None:
        if not schema_name:
            raise ValueError("Schema name is required")

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
            raise DBSessionError(f"Session error on schema '{self.schema_name}': {e}")
        finally:
            db.close()

    def create(self, model: ModelT) -> ModelT:
        with self.session() as db:
            db.add(model)
            db.flush()
            db.refresh(model)
            return model

    def create_many(self, models: Iterable[ModelT]) -> list[ModelT]:
        models = list(models)

        if not models:
            return []

        with self.session() as db:
            db.add_all(models)
            db.flush()

            for model in models:
                db.refresh(model)

            return models

    def get_by_id(self, model_class: type[ModelT], record_id: int) -> ModelT | None:
        with self.session() as db:
            return db.get(model_class, record_id)

    def get_by_filter(
        self,
        model_class: type[ModelT],
        filters: dict[str, object],
        *,
        offset: int = 0,
        limit: int | None = None,
    ) -> list[ModelT]:
        with self.session() as db:
            query = db.query(model_class).filter_by(**filters).offset(offset)
            if limit is not None:
                query = query.limit(limit)
            return query.all()

    @staticmethod
    def _apply_updates(model: ModelT, values: dict[str, object]) -> None:
        mapped_fields = set(inspect(type(model)).column_attrs.keys())
        unknown_fields = values.keys() - mapped_fields

        if unknown_fields:
            raise ValueError(f"Champs inconnus : {', '.join(sorted(unknown_fields))}")

        for key, value in values.items():
            setattr(model, key, value)

    def update(self, model: ModelT, values: dict[str, object]) -> ModelT:
        with self.session() as db:
            merged = db.merge(model)
            self._apply_updates(merged, values)
            db.flush()
            db.refresh(merged)
            return merged

    def update_by_id(
        self,
        model_class: type[ModelT],
        record_id: int,
        values: dict[str, object],
    ) -> ModelT | None:
        with self.session() as db:
            record = db.get(model_class, record_id)
            if record is None:
                return None
            self._apply_updates(record, values)
            db.flush()
            db.refresh(record)
            return record

    def delete(self, model: ModelT) -> None:
        with self.session() as db:
            merged = db.merge(model)
            db.delete(merged)

    def delete_by_id(self, model_class: type[ModelT], record_id: int) -> bool:
        with self.session() as db:
            record = db.get(model_class, record_id)
            if record is None:
                return False
            db.delete(record)
            return True

    def delete_by_filter(self, model_class: type[ModelT], filters: dict[str, object]) -> int:
        if not filters:
            raise ValueError("A filter is required at least")
        with self.session() as db:
            count = db.query(model_class).filter_by(**filters).delete()
            return count
