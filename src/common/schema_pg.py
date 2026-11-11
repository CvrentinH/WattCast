from collections.abc import Generator, Sequence
from contextlib import contextmanager
from typing import TypeVar

from sqlalchemy import text
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
			raise DBSessionError(f"Session error on schema '{self.schema_name}': {e}") from e
		finally:
			db.close()

	# ──────────────────────────────────────────────
	# CREATE
	# ──────────────────────────────────────────────

	def create(self, model: ModelT) -> ModelT:
		"""
		Insert a single ORM model instance.

		Args:
			model: A SQLAlchemy ORM instance to persist.

		Returns:
			The persisted model instance (with generated fields populated).
		"""
		with self.session() as db:
			db.add(model)
			db.flush()
			db.refresh(model)
			return model

	def create_many(self, models: Sequence[ModelT]) -> list[ModelT]:
		"""
		Insert multiple ORM model instances in a single transaction.

		Args:
			models: A sequence of SQLAlchemy ORM instances.

		Returns:
			The list of persisted model instances.
		"""
		with self.session() as db:
			db.add_all(models)
			db.flush()
			for m in models:
				db.refresh(m)
			return list(models)

	# ──────────────────────────────────────────────
	# READ
	# ──────────────────────────────────────────────

	def get_by_id(self, model_class: type[ModelT], record_id: object) -> ModelT | None:
		"""
		Fetch a single row by its primary key.

		Args:
			model_class: The ORM model class (e.g. ``BronzeBatch``).
			record_id: Primary key value.

		Returns:
			The model instance, or ``None`` if not found.
		"""
		with self.session() as db:
			return db.get(model_class, record_id)

	def get_all(
		self,
		model_class: type[ModelT],
		*,
		offset: int = 0,
		limit: int | None = None,
	) -> list[ModelT]:
		"""
		Fetch all rows of a given model, with optional pagination.

		Args:
			model_class: The ORM model class.
			offset: Number of rows to skip.
			limit: Maximum number of rows to return (``None`` = unlimited).

		Returns:
			A list of model instances.
		"""
		with self.session() as db:
			query = db.query(model_class).offset(offset)
			if limit is not None:
				query = query.limit(limit)
			return query.all()

	def get_by_filter(
		self,
		model_class: type[ModelT],
		filters: dict[str, object],
		*,
		offset: int = 0,
		limit: int | None = None,
	) -> list[ModelT]:
		"""
		Fetch rows matching column equality filters.

		Args:
			model_class: The ORM model class.
			filters: ``{column_name: value}`` pairs used as WHERE conditions.
			offset: Number of rows to skip.
			limit: Maximum number of rows to return.

		Returns:
			A list of matching model instances.
		"""
		with self.session() as db:
			query = db.query(model_class).filter_by(**filters).offset(offset)
			if limit is not None:
				query = query.limit(limit)
			return query.all()

	def count(self, model_class: type[ModelT]) -> int:
		"""
		Return the total row count for a model's table.

		Args:
			model_class: The ORM model class.

		Returns:
			Row count as an integer.
		"""
		with self.session() as db:
			return db.query(model_class).count()

	def exists(self, model_class: type[ModelT], record_id: object) -> bool:
		"""
		Check whether a row with the given primary key exists.

		Args:
			model_class: The ORM model class.
			record_id: Primary key value.

		Returns:
			``True`` if the row exists.
		"""
		with self.session() as db:
			return db.get(model_class, record_id) is not None

	def table_exists(self, table_name: str) -> bool:
		"""
		Check whether a table exists in this schema via ``information_schema``.

		Args:
			table_name: Table name (without schema prefix).

		Returns:
			``True`` if the table exists.
		"""
		query = text(
			"SELECT EXISTS ("
			"  SELECT 1 FROM information_schema.tables"
			"  WHERE table_schema = :schema AND table_name = :table"
			")"
		)
		with self.session() as db:
			result = db.execute(query, {"schema": self.schema_name, "table": table_name})
			return result.scalar_one()

	# ──────────────────────────────────────────────
	# UPDATE
	# ──────────────────────────────────────────────

	def update(self, model: ModelT, values: dict[str, object]) -> ModelT:
		"""
		Update an attached model instance with the given values.

		Args:
			model: An ORM instance (must have a primary key set).
			values: ``{column_name: new_value}`` pairs to apply.

		Returns:
			The updated model instance.
		"""
		with self.session() as db:
			merged = db.merge(model)
			for key, value in values.items():
				setattr(merged, key, value)
			db.flush()
			db.refresh(merged)
			return merged

	def update_by_id(
		self,
		model_class: type[ModelT],
		record_id: object,
		values: dict[str, object],
	) -> ModelT | None:
		"""
		Update a row by its primary key.

		Args:
			model_class: The ORM model class.
			record_id: Primary key value of the row to update.
			values: ``{column_name: new_value}`` pairs to apply.

		Returns:
			The updated model instance, or ``None`` if not found.
		"""
		with self.session() as db:
			record = db.get(model_class, record_id)
			if record is None:
				return None
			for key, value in values.items():
				setattr(record, key, value)
			db.flush()
			db.refresh(record)
			return record

	# ──────────────────────────────────────────────
	# DELETE
	# ──────────────────────────────────────────────

	def delete(self, model: ModelT) -> None:
		"""
		Delete a single ORM model instance.

		Args:
			model: The ORM instance to remove.
		"""
		with self.session() as db:
			merged = db.merge(model)
			db.delete(merged)

	def delete_by_id(self, model_class: type[ModelT], record_id: object) -> bool:
		"""
		Delete a row by its primary key.

		Args:
			model_class: The ORM model class.
			record_id: Primary key value.

		Returns:
			``True`` if a row was deleted, ``False`` if not found.
		"""
		with self.session() as db:
			record = db.get(model_class, record_id)
			if record is None:
				return False
			db.delete(record)
			return True

	def delete_by_filter(self, model_class: type[ModelT], filters: dict[str, object]) -> int:
		"""
		Delete all rows matching column equality filters.

		Args:
			model_class: The ORM model class.
			filters: ``{column_name: value}`` pairs used as WHERE conditions.

		Returns:
			Number of rows deleted.
		"""
		with self.session() as db:
			count = db.query(model_class).filter_by(**filters).delete()
			return count

	def truncate(self) -> None:
		"""
		Truncate all rows from all tables in this schema.

		Uses raw SQL ``TRUNCATE ... CASCADE``.
		"""
		query = text(
			"SELECT table_name FROM information_schema.tables "
			"WHERE table_schema = :schema AND table_type = 'BASE TABLE'"
		)
		with self.session() as db:
			result = db.execute(query, {"schema": self.schema_name})
			tables = [row[0] for row in result]
			for table in tables:
				db.execute(text(f'TRUNCATE TABLE "{self.schema_name}"."{table}" CASCADE'))
