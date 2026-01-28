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
    migrate_add_custodians()
    migrate_add_custodian_id_column()
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


def migrate_add_custodians():
    """
    Migration to add custodians table and populate with default custodians.
    This is idempotent - safe to run multiple times.
    """
    try:
        # Import here to avoid circular dependency
        from models import Custodian

        # Create all tables (including custodians if it doesn't exist)
        Base.metadata.create_all(bind=engine)

        # Check if we need to add default custodians
        db = SessionLocal()
        try:
            existing_count = db.query(Custodian).count()

            if existing_count == 0:
                logger.info("Adding default custodians...")

                default_custodians = [
                    {'name': 'GBM', 'type': 'broker', 'notes': 'Grupo Bursátil Mexicano'},
                    {'name': 'Kuspit', 'type': 'broker', 'notes': 'Casa de bolsa digital'},
                    {'name': 'Actinver', 'type': 'broker', 'notes': 'Casa de bolsa'},
                    {'name': 'BBVA Trader', 'type': 'broker', 'notes': 'Plataforma de inversión BBVA'},
                    {'name': 'Cetesdirecto', 'type': 'government', 'notes': 'Plataforma gubernamental'},
                    {'name': 'Hey Banco', 'type': 'bank', 'notes': 'Banco digital'},
                    {'name': 'Nu Invest', 'type': 'broker', 'notes': 'Inversiones Nu'},
                    {'name': 'Binance', 'type': 'crypto_exchange', 'notes': 'Exchange de criptomonedas'},
                    {'name': 'Otro', 'type': 'other', 'notes': 'Otro custodio'}
                ]

                for custodian_data in default_custodians:
                    custodian = Custodian(**custodian_data)
                    db.add(custodian)

                db.commit()
                logger.info(f"✅ {len(default_custodians)} custodios inicializados correctamente")
            else:
                logger.debug(f"Custodians table already populated with {existing_count} entries")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error during custodians migration: {str(e)}")
        # Don't raise - allow app to continue even if migration fails


def migrate_add_custodian_id_column():
    """
    Migration to add custodian_id foreign key column to transactions table.
    This is idempotent - safe to run multiple times.
    """
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("PRAGMA table_info(transactions)"))
            columns = [row[1] for row in result]

            if 'custodian_id' not in columns:
                logger.info("Adding 'custodian_id' column to transactions table")
                # Add the custodian_id column
                conn.execute(text("ALTER TABLE transactions ADD COLUMN custodian_id INTEGER"))
                conn.commit()
                logger.info("Migration completed: 'custodian_id' column added")
            else:
                logger.debug("'custodian_id' column already exists, skipping migration")

    except Exception as e:
        logger.error(f"Error during custodian_id migration: {str(e)}")
        # Don't raise - allow app to continue even if migration fails
