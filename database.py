"""Database initialization and configuration."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'portfolio.db')
DATABASE_URI = f'sqlite:///{DATABASE_PATH}'

# Create engine
engine = create_engine(DATABASE_URI, echo=False)

# Create session factory
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db():
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(bind=engine)
    migrate_add_market_column()
    print(f"Database initialized at: {DATABASE_PATH}")


def migrate_add_market_column():
    """
    Migration to add 'market' column to existing transactions table.
    This is idempotent - safe to run multiple times.
    """
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("PRAGMA table_info(transactions)"))
            columns = [row[1] for row in result]

            if 'market' not in columns:
                logger.info("Adding 'market' column to transactions table")
                # Add the market column with default value 'MX'
                conn.execute(text("ALTER TABLE transactions ADD COLUMN market TEXT DEFAULT 'MX'"))
                conn.commit()
                logger.info("Migration completed: 'market' column added")

                # Update currency to MXN for all existing records
                conn.execute(text("UPDATE transactions SET currency = 'MXN' WHERE currency IS NULL OR currency = 'USD'"))
                conn.commit()
                logger.info("Updated all transactions to use MXN currency")
            else:
                logger.debug("'market' column already exists, skipping migration")

    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        # Don't raise - allow app to continue even if migration fails

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
