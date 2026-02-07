#!/usr/bin/env python3
"""Script de prueba para validar que la API funcione con criptomonedas"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_add_crypto_transaction():
    """Prueba agregar una transacción de BTC"""
    print("=" * 70)
    print("TEST: Agregar transacción de BTC")
    print("=" * 70)

    transaction_data = {
        "market": "CRYPTO",
        "ticker": "BTC",
        "purchase_date": "2024-01-15",
        "purchase_price": 750000.00,  # En MXN
        "quantity": 0.05234567  # 8 decimales
    }

    print(f"\nDatos a enviar:")
    print(json.dumps(transaction_data, indent=2))

    response = requests.post(
        f"{BASE_URL}/api/transactions",
        json=transaction_data,
        headers={"Content-Type": "application/json"}
    )

    print(f"\nRespuesta del servidor (HTTP {response.status_code}):")
    print(json.dumps(response.json(), indent=2))

    if response.status_code == 201:
        print("\n✅ Transacción creada exitosamente!")
        return response.json()['transaction']['id']
    else:
        print("\n❌ Error al crear transacción")
        return None

def test_get_transactions():
    """Prueba obtener todas las transacciones"""
    print("\n" + "=" * 70)
    print("TEST: Obtener todas las transacciones")
    print("=" * 70)

    response = requests.get(f"{BASE_URL}/api/transactions")

    print(f"\nRespuesta del servidor (HTTP {response.status_code}):")
    transactions = response.json()

    if transactions:
        print(f"\nTotal de transacciones: {len(transactions)}")

        # Buscar transacciones de crypto
        crypto_txs = [t for t in transactions if t.get('market') == 'CRYPTO']
        print(f"Transacciones de crypto: {len(crypto_txs)}")

        if crypto_txs:
            print("\nDetalles de transacciones crypto:")
            for tx in crypto_txs:
                print(f"\n  Ticker: {tx['ticker']}")
                print(f"  Cantidad: {tx['quantity']}")
                print(f"  Precio de compra: ${tx['purchase_price']:,.2f} MXN")
                print(f"  Precio actual: ${tx['current_price']:,.2f} MXN" if tx['current_price'] else "  Precio actual: N/A")
                print(f"  Valor invertido: ${tx['invested_value']:,.2f} MXN")
                print(f"  Valor actual: ${tx['current_value']:,.2f} MXN" if tx['current_value'] else "  Valor actual: N/A")

                if tx['gain_loss_dollar'] is not None:
                    sign = "+" if tx['gain_loss_dollar'] >= 0 else ""
                    print(f"  Ganancia/Pérdida: {sign}${tx['gain_loss_dollar']:,.2f} MXN ({tx['gain_loss_percent']:.2f}%)")
                else:
                    print(f"  Ganancia/Pérdida: N/A")

            return True
        else:
            print("\n⚠️  No hay transacciones de crypto")
            return False
    else:
        print("\n⚠️  No hay transacciones en el sistema")
        return False

def test_portfolio_summary():
    """Prueba obtener resumen del portfolio"""
    print("\n" + "=" * 70)
    print("TEST: Resumen del portfolio")
    print("=" * 70)

    response = requests.get(f"{BASE_URL}/api/portfolio/summary")

    print(f"\nRespuesta del servidor (HTTP {response.status_code}):")
    data = response.json()

    print(f"\nTotales del portfolio:")
    totals = data.get('totals', {})
    print(f"  Total invertido: ${totals.get('total_invested', 0):,.2f} MXN")
    print(f"  Valor actual: ${totals.get('total_current_value', 0):,.2f} MXN")
    print(f"  Ganancia/Pérdida: ${totals.get('total_gain_loss_dollar', 0):,.2f} MXN ({totals.get('total_gain_loss_percent', 0):.2f}%)")

    positions = data.get('positions', [])
    print(f"\nPosiciones: {len(positions)}")

    if positions:
        print("\nDetalles de posiciones:")
        for pos in positions:
            print(f"\n  {pos['ticker']}:")
            print(f"    Cantidad: {pos['total_quantity']}")
            print(f"    Precio promedio: ${pos['avg_purchase_price']:,.2f} MXN")
            print(f"    Precio actual: ${pos['current_price']:,.2f} MXN" if pos['current_price'] else "    Precio actual: N/A")
            print(f"    Valor actual: ${pos['current_value']:,.2f} MXN" if pos['current_value'] else "    Valor actual: N/A")

if __name__ == "__main__":
    print("\n🧪 INICIANDO PRUEBAS DE API CRYPTO\n")

    # Prueba 1: Agregar transacción BTC
    tx_id = test_add_crypto_transaction()

    # Prueba 2: Obtener transacciones (debe incluir precios actuales)
    has_crypto = test_get_transactions()

    # Prueba 3: Obtener resumen del portfolio
    test_portfolio_summary()

    print("\n" + "=" * 70)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 70)

    if has_crypto:
        print("\n✨ El sistema está funcionando correctamente con criptomonedas!")
        print("\nPuedes verificar en el navegador:")
        print("  → http://localhost:5000")
        print("\nLas cryptos deberían mostrar:")
        print("  • Emoji 🪙 junto al ticker")
        print("  • Cantidad con 8 decimales")
        print("  • Precios actuales en MXN")
    else:
        print("\n⚠️  No se encontraron transacciones de crypto después de la prueba")
