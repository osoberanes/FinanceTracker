"""SQLAlchemy models for the portfolio tracker."""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Transaction(Base):
    """Model for stock transactions."""

    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_type = Column(String, nullable=False, default='stock')  # Future: 'stock', 'crypto', 'cete', 'bond'
    ticker = Column(String, nullable=False)
    purchase_date = Column(Date, nullable=False)
    purchase_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    currency = Column(String, default='USD')  # Future: 'USD', 'MXN'
    custodian = Column(String)  # Future: 'GBM', 'Binance', etc.
    commission = Column(Float, default=0.0)  # Future
    notes = Column(Text)  # Future
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'asset_type': self.asset_type,
            'ticker': self.ticker,
            'purchase_date': self.purchase_date.strftime('%Y-%m-%d') if self.purchase_date else None,
            'purchase_price': self.purchase_price,
            'quantity': self.quantity,
            'currency': self.currency,
            'custodian': self.custodian,
            'commission': self.commission,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f"<Transaction(ticker='{self.ticker}', date='{self.purchase_date}', quantity={self.quantity})>"
