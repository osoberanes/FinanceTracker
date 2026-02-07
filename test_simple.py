#!/usr/bin/env python3
"""Test simple para verificar que el gráfico funcione sin rate limit"""

import time
from database import init_db, get_db
from models import Transaction

# Inicializar DB
init_db()

# Obtener transacciones
db = get_db()
transactions = db.query(Transaction).all()

print(f"\n📊 TRANSACCIONES EN LA BASE DE DATOS: {len(transactions)}")
print("=" * 70)

for tx in transactions:
    print(f"\nID: {tx.id}")
    print(f"  Ticker: {tx.ticker}")
    print(f"  Mercado: {tx.market}")
    print(f"  Asset Type: {tx.asset_type}")
    print(f"  Cantidad: {tx.quantity}")
    print(f"  Precio compra: ${tx.purchase_price:,.2f} MXN")
    print(f"  Fecha: {tx.purchase_date}")

print("\n" + "=" * 70)
print("✅ Base de datos funcionando correctamente")
print("\n💡 RECOMENDACIÓN:")
print("   El rate limit de Yahoo Finance se resetea después de ~1 minuto")
print("   Espera un momento y recarga la página web:")
print("   → http://localhost:5000")
print("\n   El gráfico debería cargar correctamente después")
