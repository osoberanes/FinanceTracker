"""SQLAlchemy models for the portfolio tracker."""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Custodian(Base):
    """Model for custodians (brokers, banks, exchanges)."""

    __tablename__ = 'custodians'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(50))  # 'broker', 'bank', 'crypto_exchange', 'government', 'other'
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with transactions
    transactions = relationship('Transaction', backref='custodian_obj', lazy=True)

    def __repr__(self):
        return f'<Custodian {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Transaction(Base):
    """Model for stock transactions."""

    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_type = Column(String, nullable=False, default='stock')  # 'stock', 'crypto', 'cete', 'bond'
    ticker = Column(String, nullable=False)
    market = Column(String, default='MX')  # 'MX' for Mexico (BMV), 'US' for United States, 'CRYPTO' for crypto
    transaction_type = Column(String(10), nullable=False, default='buy')  # 'buy' or 'sell'
    purchase_date = Column(Date, nullable=False)
    purchase_price = Column(Numeric(18, 8), nullable=False)  # 8 decimals for crypto precision
    quantity = Column(Numeric(18, 8), nullable=False)  # 8 decimals for crypto precision
    currency = Column(String, default='MXN')  # All prices stored in MXN
    custodian_id = Column(Integer, ForeignKey('custodians.id'), nullable=True)  # Foreign key to custodians table
    custodian = Column(String)  # Legacy field - kept for backwards compatibility
    commission = Column(Float, default=0.0)  # Future
    notes = Column(Text)  # Future
    generates_staking = Column(Boolean, default=False)  # For ETH, SOL and other staking cryptos
    staking_rewards = Column(Numeric(18, 8), default=0.0)  # Accumulated staking rewards in crypto units

    # Clasificación Swensen - asset class for diversification analysis
    asset_class = Column(String(30), nullable=True)
    # Valores posibles: acciones_mexico, acciones_usa, acciones_internacionales,
    # mercados_emergentes, fibras, cetes, bonos_gubernamentales, udibonos,
    # oro_materias_primas, criptomonedas

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'asset_type': self.asset_type,
            'ticker': self.ticker,
            'market': self.market,
            'transaction_type': self.transaction_type,
            'purchase_date': self.purchase_date.strftime('%Y-%m-%d') if self.purchase_date else None,
            'purchase_price': float(self.purchase_price) if self.purchase_price else None,
            'quantity': float(self.quantity) if self.quantity else None,
            'currency': self.currency,
            'custodian': self.custodian,
            'custodian_id': self.custodian_id,
            'commission': self.commission,
            'notes': self.notes,
            'generates_staking': self.generates_staking,
            'staking_rewards': float(self.staking_rewards) if self.staking_rewards else 0.0,
            'asset_class': self.asset_class,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f"<Transaction(ticker='{self.ticker}', date='{self.purchase_date}', quantity={self.quantity})>"


class SwensenConfig(Base):
    """Configuracion personalizada del modelo Swensen para diversificacion."""

    __tablename__ = 'swensen_config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_class = Column(String(30), nullable=False, unique=True)
    target_percentage = Column(Numeric(5, 2), nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SwensenConfig {self.asset_class}: {self.target_percentage}%>'

    def to_dict(self):
        return {
            'id': self.id,
            'asset_class': self.asset_class,
            'target_percentage': float(self.target_percentage) if self.target_percentage else 0,
            'is_active': self.is_active,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
