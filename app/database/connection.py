from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# ============================================================================
# DATABASE ENGINE CONFIGURATION
# ============================================================================
# The engine is the starting point for any SQLAlchemy application.
# It manages the connection pool and provides a source of database connectivity.

engine = create_engine(
    settings.DATABASE_URL,  # PostgreSQL connection string from .env
    pool_pre_ping=True,     # Tests connections before using them from the pool
                            # This prevents using stale/closed connections
    echo=False,             # If True, logs all SQL statements (useful for debugging)
)

# ============================================================================
# DECLARATIVE BASE
# ============================================================================
# Base class for all SQLAlchemy models. All model classes must inherit from this.
# It maintains a registry of all model classes and their table metadata.

Base = declarative_base()


def get_engine():
    """
    Get the database engine instance.

    Returns:
        Engine: SQLAlchemy engine object
    """
    return engine


def init_db():
    """
    Initialize the database by creating all tables.

    This function creates all tables that are defined in models that inherit
    from Base. It will only create tables that don't already exist.

    Note: In production, use Alembic migrations instead of this function.
    """
    Base.metadata.create_all(bind=engine)


def close_db():
    """
    Close all database connections and dispose of the connection pool.

    This should be called during application shutdown to properly clean up
    all database resources.
    """
    engine.dispose()
