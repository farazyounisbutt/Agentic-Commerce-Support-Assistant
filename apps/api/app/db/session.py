from collections.abc import Generator

from pgvector.psycopg import register_vector
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)


@event.listens_for(engine, "connect")
def register_pgvector(dbapi_connection: object, connection_record: object) -> None:
    """Register pgvector's psycopg codec for vector query parameters and results."""
    register_vector(dbapi_connection)


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session for future request handlers."""
    with SessionLocal() as session:
        yield session

