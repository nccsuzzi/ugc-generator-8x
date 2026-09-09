from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Engine configuration with connection pooling
engine = create_engine(
    settings.sync_database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they do not already exist."""
    import logging
    import app.models  # Ensure all models are imported before creating tables
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"Database initialization deferred (database not ready: {e})"
        )

