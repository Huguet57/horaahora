from datetime import UTC, datetime

from sqlalchemy.engine import Engine

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.models import Base


def resolve_engine(database: Database | Engine | str) -> tuple[Database | None, Engine]:
    if isinstance(database, Database):
        resolved_database = database
        engine = database.engine
    elif isinstance(database, Engine):
        resolved_database = None
        engine = database
    else:
        resolved_database = Database(database)
        engine = resolved_database.engine
    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(engine)
    return resolved_database, engine


def database_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def domain_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
