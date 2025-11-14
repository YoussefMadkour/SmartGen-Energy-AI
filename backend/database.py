"""
Database configuration and initialization for the Energy Optimization ROI Dashboard.

This module handles:
- SQLite database connection setup
- Table creation and schema management
- Database session management
"""

import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool


# Get database URL from environment variable with fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/telemetry.db")

# Ensure data directory exists for SQLite database
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

# Create engine with SQLite-specific settings
# StaticPool is used for SQLite to handle concurrent access in async context
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Allow multi-threaded access
    poolclass=StaticPool,  # Use static pool for SQLite
    echo=False  # Set to True for SQL query logging during development
)


def init_database() -> None:
    """
    Initialize the database by creating all tables defined in SQLModel.
    
    This function should be called on application startup to ensure
    the database schema is properly set up.
    
    Creates:
        - telemetry table with indexed timestamp column
    """
    SQLModel.metadata.create_all(engine)
    print(f"Database initialized at {DATABASE_URL}")


def get_session() -> Session:
    """
    Create a new database session.
    
    Returns:
        Session: SQLModel session for database operations
        
    Usage:
        with get_session() as session:
            # Perform database operations
            session.add(reading)
            session.commit()
    """
    return Session(engine)


def get_db_session():
    """
    Dependency function for FastAPI to inject database sessions.
    
    Yields:
        Session: Database session that will be automatically closed
        
    Usage in FastAPI:
        @app.get("/endpoint")
        def endpoint(session: Session = Depends(get_db_session)):
            # Use session here
    """
    with get_session() as session:
        yield session
