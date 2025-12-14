"""
Database Module
===============
This module sets up the database connection and session management using SQLAlchemy.
It provides the database engine, session factory, and base class for all models.

Key Components:
- Engine: Manages database connections
- SessionLocal: Factory for creating database sessions
- Base: Base class for all database models
- get_db: Dependency injection function for FastAPI routes
- init_db: Initializes database tables
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

# Load application settings
settings = get_settings()

# Create SQLAlchemy Engine
# ========================
# The engine is the starting point for any SQLAlchemy application.
# It manages the connection pool and dialect for the database.
engine = create_engine(
    settings.database_url,
    # SQLite specific: Allow multiple threads to use the same connection
    # This is needed because FastAPI is async and may use multiple threads
    connect_args={"check_same_thread": False}
)

# Create Session Factory
# ======================
# SessionLocal is a factory that creates new database sessions.
# Each session represents a "workspace" for database operations.
SessionLocal = sessionmaker(
    autocommit=False,  # Don't auto-commit changes (we control transactions)
    autoflush=False,   # Don't auto-flush changes (we control when to flush)
    bind=engine        # Bind to our database engine
)

# Create Base Class for Models
# ============================
# All database models will inherit from this Base class.
# It provides the metadata and table mapping functionality.
Base = declarative_base()


def get_db():
    """
    Database Session Dependency
    
    This function is used as a FastAPI dependency to provide database sessions
    to route handlers. It ensures proper session lifecycle management:
    1. Creates a new session for each request
    2. Yields the session to the route handler
    3. Closes the session after the request completes (even if an error occurs)
    
    Usage in FastAPI routes:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        Session: SQLAlchemy database session
    """
    # Create a new database session
    db = SessionLocal()
    try:
        # Provide the session to the route handler
        yield db
    finally:
        # Always close the session when done (cleanup)
        # This happens even if an exception occurs
        db.close()


def init_db():
    """
    Initialize Database Tables
    
    This function creates all database tables defined in our models.
    It should be called once when the application starts.
    
    How it works:
    1. Reads all model classes that inherit from Base
    2. Creates corresponding tables in the database
    3. If tables already exist, it does nothing (safe to call multiple times)
    
    Note: This is suitable for development. In production, use migrations
    (e.g., Alembic) for better database schema management.
    """
    # Create all tables defined in models
    # Base.metadata contains information about all tables
    Base.metadata.create_all(bind=engine)
