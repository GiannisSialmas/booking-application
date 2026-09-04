from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
# pool_size/max_overflow are set explicitly (SQLAlchemy defaults to the same
# values) so the concurrency ceiling is visible in code rather than implicit:
# 5 connections stay open and ready at all times; under burst load up to 10
# more are opened temporarily, for a hard ceiling of 15 concurrent DB
# connections before a request has to wait.
engine = create_engine(settings.database_url, pool_size=5, max_overflow=10)
SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session() -> Generator[Session, None, None]:
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()
