#!/usr/bin/env python3
"""Script para verificar datos de ejemplo cargados"""

from database import get_db
from models import Transaction

db = get_db()
transactions = db.query(Transaction).order_by(Transaction.purchase_date.desc()).all()

print(f'\n📊 TRANSACCIONES CARGADAS: {len(transactions)}\n')
print(f'{"Fecha":<12} {"Ticker":<15} {"Cantidad":<12} {"Precio":<15} {"Mercado":<8} {"Asset Class":<20}')
print('=' * 95)

for t in transactions[:5]:
    print(f'{str(t.purchase_date):<12} {t.ticker:<15} {t.quantity:<12.8f} ${t.purchase_price:<14,.2f} {t.market:<8} {t.asset_class or "N/A":<20}')

print(f'\n... (mostrando primeras 5 de {len(transactions)})')

# Contar por tipo
stocks = sum(1 for t in transactions if t.asset_type == 'stock')
cryptos = sum(1 for t in transactions if t.asset_type == 'crypto')
print(f'\n✅ Stocks: {stocks}')
print(f'✅ Cryptos: {cryptos}')

# Verificar staking
staking = sum(1 for t in transactions if t.generates_staking)
print(f'✅ Con staking: {staking}')

# Verificar custodios
with_custodian = sum(1 for t in transactions if t.custodian_id is not None)
print(f'✅ Con custodio asignado: {with_custodian}')

db.close()
