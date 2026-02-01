#!/usr/bin/env python3
"""
Script para corregir formato de tickers mexicanos
Convierte VWOMX → VWO.MX, FUNO11MX → FUNO11.MX, etc.
"""

from database import init_db, get_db
from models import Transaction
import re

def fix_mexican_tickers():
    """Corrige tickers mexicanos que no tienen el punto"""

    # Inicializar DB
    init_db()
    db = get_db()

    try:
        # Obtener todas las transacciones del mercado MX
        mx_transactions = db.query(Transaction).filter_by(market='MX').all()

        if not mx_transactions:
            print("ℹ️  No hay transacciones del mercado MX")
            return

        print(f"📊 Revisando {len(mx_transactions)} transacciones del mercado MX...\n")

        fixed_count = 0

        for txn in mx_transactions:
            ticker = txn.ticker

            # Si el ticker termina en MX pero no tiene punto
            if ticker.endswith('MX') and '.MX' not in ticker:
                # Extraer el símbolo base (todo menos MX)
                base_symbol = ticker[:-2]  # Quita "MX"

                # Formar ticker correcto
                correct_ticker = f"{base_symbol}.MX"

                print(f"  Corrigiendo: {ticker:20} → {correct_ticker}")

                txn.ticker = correct_ticker
                fixed_count += 1
            elif not ticker.endswith('.MX'):
                # Si no termina en .MX, agregarlo
                correct_ticker = f"{ticker}.MX"
                print(f"  Corrigiendo: {ticker:20} → {correct_ticker}")
                txn.ticker = correct_ticker
                fixed_count += 1

        if fixed_count > 0:
            db.commit()
            print(f"\n✅ {fixed_count} tickers corregidos exitosamente")
        else:
            print("\n✅ Todos los tickers ya tienen el formato correcto")

        # Mostrar resumen
        print("\n📋 TICKERS ACTUALES:")
        current_tickers = db.query(Transaction.ticker).filter_by(market='MX').distinct().all()
        for (ticker,) in current_tickers:
            print(f"  • {ticker}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    print("="*60)
    print("🔧 CORRECCIÓN DE FORMATO DE TICKERS MEXICANOS")
    print("="*60)
    print()

    fix_mexican_tickers()

    print()
    print("="*60)
