"""Database initialization and configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'portfolio.db')
DATABASE_URI = f'sqlite:///{DATABASE_PATH}'

# Create engine
engine = create_engine(DATABASE_URI, echo=False)

# Create session factory
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DATABASE_PATH}")

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise

def close_db():
    """Close database session."""
    SessionLocal.remove()
