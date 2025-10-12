from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.database.connection import engine

# ============================================================================
# SESSION FACTORY
# ============================================================================
# sessionmaker is a factory for creating Session objects.
# Sessions are used to interact with the database (queries, inserts, etc.)

SessionLocal = sessionmaker(
    autocommit=False,  # Don't auto-commit transactions. We control when to commit.
                       # This allows us to rollback if something goes wrong.

    autoflush=False,   # Don't automatically flush changes to the database.
                       # Flush is when pending changes are sent to the database
                       # but not yet committed. We control when to flush.

    bind=engine        # Bind this session factory to our database engine.
                       # All sessions created by this factory will use this engine.
)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI routes.

    This is a generator function that yields a database session and ensures
    it's properly closed after the request is completed, even if an error occurs.

    FastAPI's Depends() will automatically:
    1. Create a new session before the request
    2. Inject it into your route function
    3. Close it after the request (even if an exception occurred)

    Usage in FastAPI routes:
        @router.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users

    Yields:
        Session: SQLAlchemy database session

    Note: Each request gets its own independent session.
    """
    db = SessionLocal()  # Create a new session
    try:
        yield db  # Provide the session to the route
    finally:
        db.close()  # Always close the session, even if an error occurred


def get_db_session() -> Session:
    """
    Get a database session directly (not as FastAPI dependency).

    Use this when you need a session outside of FastAPI routes,
    such as in background tasks, CLI scripts, or tests.

    IMPORTANT: You are responsible for closing the session when done!

    Usage example:
        db = get_db_session()
        try:
            user = db.query(User).filter(User.email == "test@example.com").first()
            # Do something with user
            db.commit()  # Commit changes if any
        except Exception as e:
            db.rollback()  # Rollback on error
            raise e
        finally:
            db.close()  # Always close the session

    Returns:
        Session: SQLAlchemy database session
    """
    return SessionLocal()
