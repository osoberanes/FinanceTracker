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
    migrate_add_crypto_fields()
    migrate_add_asset_class_column()
    migrate_add_swensen_config()
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
                    {'name': 'Bitso', 'type': 'crypto_exchange', 'notes': 'Exchange mexicano de criptomonedas'},
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


def migrate_add_crypto_fields():
    """
    Migration to add crypto-specific fields to transactions table.
    Adds: generates_staking (BOOLEAN) and staking_rewards (NUMERIC).
    This is idempotent - safe to run multiple times.
    """
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("PRAGMA table_info(transactions)"))
            columns = [row[1] for row in result]

            if 'generates_staking' not in columns:
                logger.info("Adding 'generates_staking' column to transactions table")
                conn.execute(text("ALTER TABLE transactions ADD COLUMN generates_staking BOOLEAN DEFAULT 0"))
                conn.commit()
                logger.info("Migration completed: 'generates_staking' column added")
            else:
                logger.debug("'generates_staking' column already exists, skipping")

            if 'staking_rewards' not in columns:
                logger.info("Adding 'staking_rewards' column to transactions table")
                conn.execute(text("ALTER TABLE transactions ADD COLUMN staking_rewards NUMERIC DEFAULT 0.0"))
                conn.commit()
                logger.info("Migration completed: 'staking_rewards' column added")
            else:
                logger.debug("'staking_rewards' column already exists, skipping")

    except Exception as e:
        logger.error(f"Error during crypto fields migration: {str(e)}")
        # Don't raise - allow app to continue even if migration fails


def migrate_add_asset_class_column():
    """
    Migration to add asset_class column to transactions table for Swensen classification.
    Also classifies existing transactions.
    This is idempotent - safe to run multiple times.
    """
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("PRAGMA table_info(transactions)"))
            columns = [row[1] for row in result]

            if 'asset_class' not in columns:
                logger.info("Adding 'asset_class' column to transactions table")
                conn.execute(text("ALTER TABLE transactions ADD COLUMN asset_class TEXT"))
                conn.commit()
                logger.info("Migration completed: 'asset_class' column added")

                # Classify existing transactions
                classify_existing_transactions()
            else:
                logger.debug("'asset_class' column already exists, skipping migration")

    except Exception as e:
        logger.error(f"Error during asset_class migration: {str(e)}")
        # Don't raise - allow app to continue even if migration fails


def classify_existing_transactions():
    """
    Classify existing transactions that don't have an asset_class.
    """
    try:
        # Import here to avoid circular dependency
        from utils_classification import classify_asset

        db = SessionLocal()
        try:
            # Get all transactions without asset_class
            result = db.execute(
                text("SELECT id, ticker, market, asset_type FROM transactions WHERE asset_class IS NULL")
            )
            rows = result.fetchall()

            if not rows:
                logger.debug("No transactions need classification")
                return

            logger.info(f"Classifying {len(rows)} existing transactions...")

            for row in rows:
                trans_id = row[0]
                ticker = row[1]
                market = row[2] or 'MX'
                asset_type = row[3] or 'stock'

                asset_class = classify_asset(ticker, market, asset_type)

                if asset_class:
                    db.execute(
                        text("UPDATE transactions SET asset_class = :asset_class WHERE id = :id"),
                        {"asset_class": asset_class, "id": trans_id}
                    )

            db.commit()
            logger.info(f"Successfully classified {len(rows)} transactions")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error classifying existing transactions: {str(e)}")


def migrate_add_swensen_config():
    """
    Migration to create swensen_config table and populate with default values.
    This is idempotent - safe to run multiple times.
    """
    try:
        from models import SwensenConfig
        from utils_classification import initialize_default_swensen_config

        # Create all tables (including swensen_config if it doesn't exist)
        Base.metadata.create_all(bind=engine)

        db = SessionLocal()
        try:
            # Check if we need to add default config
            existing_count = db.query(SwensenConfig).count()

            if existing_count == 0:
                logger.info("Initializing default Swensen configuration...")
                initialize_default_swensen_config(db)
                logger.info("Swensen configuration initialized with default values")
            else:
                logger.debug(f"Swensen config table already has {existing_count} entries")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error during Swensen config migration: {str(e)}")
