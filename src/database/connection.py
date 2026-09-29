from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.settings import settings


# ============================================================
# Database Engine
# ============================================================

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)


# ============================================================
# Database Session
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ============================================================
# Database Dependency
# ============================================================

def get_db():
    """
    Provide a database session to FastAPI endpoints.

    The session is automatically closed after
    the request is completed.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# Create Database Tables
# ============================================================

def create_tables():
    """
    Create all SQLAlchemy tables defined in the models.
    """

    # Import models so SQLAlchemy registers them with Base.metadata.
    from src.database import models
    from src.database.base import Base

    Base.metadata.create_all(bind=engine)