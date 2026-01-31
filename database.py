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

    # Intentar cargar datos de ejemplo (solo si LOAD_SAMPLE_DATA=true)
    load_sample_data()


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


def load_sample_data():
    """
    Carga transacciones de ejemplo para demo/testing

    Control de activación:
    - PRODUCCIÓN: No configurar LOAD_SAMPLE_DATA (o =false) → Base de datos vacía
    - DEMO/TEST: Configurar LOAD_SAMPLE_DATA=true → Carga datos de ejemplo

    Solo carga datos si:
    1. LOAD_SAMPLE_DATA=true en variables de entorno
    2. La base de datos está vacía (no hay transacciones)
    """
    import os
    from models import Transaction, Custodian
    from datetime import datetime
    from utils_classification import classify_asset

    # Verificar variable de entorno
    load_samples = os.environ.get('LOAD_SAMPLE_DATA', 'false').lower() == 'true'

    if not load_samples:
        print("ℹ️  LOAD_SAMPLE_DATA no está activado, saltando datos de ejemplo")
        return

    # Verificar si ya hay transacciones
    db = SessionLocal()
    try:
        existing = db.query(Transaction).first()
        if existing:
            print("ℹ️  Base de datos ya tiene datos, saltando carga de ejemplos")
            return

        print("📊 Cargando datos de ejemplo (LOAD_SAMPLE_DATA=true)...")

        # Obtener custodios
        gbm = db.query(Custodian).filter_by(name='GBM').first()
        bitso = db.query(Custodian).filter_by(name='Bitso').first()

        if not gbm or not bitso:
            print("⚠️  Custodios no encontrados, creando transacciones sin custodio")

        # Transacciones de ejemplo
        sample_transactions = [
            {'date': '2025-11-26', 'ticker': 'NVONLMX', 'price': 895.94, 'qty': 5.0, 'market': 'MX', 'custodian': gbm},
            {'date': '2025-09-29', 'ticker': 'PAXG', 'price': 70000.00, 'qty': 0.05, 'market': 'CRYPTO', 'custodian': bitso},
            {'date': '2025-08-15', 'ticker': 'VWOMX', 'price': 976.00, 'qty': 15.0, 'market': 'MX', 'custodian': gbm},
            {'date': '2025-08-15', 'ticker': 'SOL', 'price': 3522.84, 'qty': 0.0636, 'market': 'CRYPTO', 'custodian': bitso},
            {'date': '2025-05-29', 'ticker': 'IAU.MX', 'price': 1208.00, 'qty': 12.0, 'market': 'MX', 'custodian': gbm},
            {'date': '2025-05-27', 'ticker': 'ETH', 'price': 52103.75, 'qty': 0.0058, 'market': 'CRYPTO', 'custodian': bitso},
            {'date': '2025-05-12', 'ticker': 'XRP', 'price': 52.38, 'qty': 13.17, 'market': 'CRYPTO', 'custodian': bitso},
            {'date': '2025-02-01', 'ticker': 'ETH', 'price': 45000.00, 'qty': 0.0025, 'market': 'CRYPTO', 'custodian': bitso},
            {'date': '2024-03-08', 'ticker': 'AGUILASCPO.MX', 'price': 27.07, 'qty': 30.0, 'market': 'MX', 'custodian': gbm},
            {'date': '2023-07-13', 'ticker': 'FUNO11MX', 'price': 25.00, 'qty': 199.0, 'market': 'MX', 'custodian': gbm},
            {'date': '2023-06-21', 'ticker': 'VOO.MX', 'price': 6955.95, 'qty': 3.0, 'market': 'MX', 'custodian': gbm},
            {'date': '2023-05-31', 'ticker': 'VOO.MX', 'price': 6800.00, 'qty': 1.0, 'market': 'MX', 'custodian': gbm},
            {'date': '2023-04-25', 'ticker': 'BTC', 'price': 502344.69, 'qty': 0.004, 'market': 'CRYPTO', 'custodian': bitso},
        ]

        # Crear transacciones
        count = 0
        for txn_data in sample_transactions:
            try:
                # Determinar asset_type
                asset_type = 'crypto' if txn_data['market'] == 'CRYPTO' else 'stock'

                # Clasificar asset_class
                asset_class = classify_asset(
                    txn_data['ticker'],
                    txn_data['market'],
                    asset_type
                )

                # Determinar si genera staking
                generates_staking = txn_data['ticker'] in ['ETH', 'SOL']

                transaction = Transaction(
                    asset_type=asset_type,
                    ticker=txn_data['ticker'],
                    market=txn_data['market'],
                    asset_class=asset_class,
                    purchase_date=datetime.strptime(txn_data['date'], '%Y-%m-%d').date(),
                    purchase_price=txn_data['price'],
                    quantity=txn_data['qty'],
                    custodian_id=txn_data['custodian'].id if txn_data['custodian'] else None,
                    generates_staking=generates_staking,
                    currency='MXN'
                )

                db.add(transaction)
                count += 1

            except Exception as e:
                print(f"⚠️  Error creando transacción {txn_data['ticker']}: {e}")

        db.commit()
        print(f"✅ {count} transacciones de ejemplo cargadas exitosamente")

    except Exception as e:
        logger.error(f"Error loading sample data: {str(e)}")
        db.rollback()
    finally:
        db.close()
