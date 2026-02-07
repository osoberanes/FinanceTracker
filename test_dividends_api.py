#!/usr/bin/env python3
"""
Script para verificar endpoints de dividendos
"""

import requests
import json
from datetime import date

BASE_URL = "http://localhost:5000"

def test_create_dividend():
    """Test crear un dividendo"""
    print("\n📝 Test: Crear dividendo...")

    data = {
        "ticker": "FUNO11.MX",
        "dividend_type": "dividend",
        "payment_date": "2024-03-15",
        "gross_amount": 180.00,
        "net_amount": 150.00,
        "notes": "Dividendo Q1 2024"
    }

    response = requests.post(f"{BASE_URL}/api/dividends", json=data)
    print(f"Status: {response.status_code}")

    if response.ok:
        result = response.json()
        print(f"✅ Dividendo creado: {result['dividend']['ticker']} - ${result['dividend']['net_amount']}")
        return result['dividend']['id']
    else:
        print(f"❌ Error: {response.text}")
        return None


def test_get_dividends():
    """Test obtener todos los dividendos"""
    print("\n📋 Test: Obtener dividendos...")

    response = requests.get(f"{BASE_URL}/api/dividends")
    print(f"Status: {response.status_code}")

    if response.ok:
        dividends = response.json()
        print(f"✅ Total dividendos: {len(dividends)}")
        for div in dividends:
            print(f"  - {div['ticker']}: ${div['net_amount']} ({div['dividend_type']}) - {div['payment_date']}")
    else:
        print(f"❌ Error: {response.text}")


def test_get_summary():
    """Test obtener resumen"""
    print("\n📊 Test: Obtener resumen...")

    response = requests.get(f"{BASE_URL}/api/dividends/summary?year=2024")
    print(f"Status: {response.status_code}")

    if response.ok:
        summary = response.json()
        print(f"✅ Resumen 2024:")
        print(f"  Total recibido: ${summary['total_dividends']}")
        print(f"  Yield: {summary['dividend_yield_percent']}%")
        print(f"  Pagos: {summary['count']}")
        print(f"  Por tipo: {summary['by_type']}")
    else:
        print(f"❌ Error: {response.text}")


def test_update_dividend(div_id):
    """Test actualizar dividendo"""
    print(f"\n✏️ Test: Actualizar dividendo {div_id}...")

    data = {
        "net_amount": 160.00,
        "notes": "Dividendo Q1 2024 (actualizado)"
    }

    response = requests.put(f"{BASE_URL}/api/dividends/{div_id}", json=data)
    print(f"Status: {response.status_code}")

    if response.ok:
        result = response.json()
        print(f"✅ Dividendo actualizado")
    else:
        print(f"❌ Error: {response.text}")


def test_delete_dividend(div_id):
    """Test eliminar dividendo"""
    print(f"\n🗑️ Test: Eliminar dividendo {div_id}...")

    response = requests.delete(f"{BASE_URL}/api/dividends/{div_id}")
    print(f"Status: {response.status_code}")

    if response.ok:
        print(f"✅ Dividendo eliminado")
    else:
        print(f"❌ Error: {response.text}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTING DIVIDENDS API")
    print("=" * 60)

    # Crear un dividendo
    div_id = test_create_dividend()

    if div_id:
        # Obtener lista
        test_get_dividends()

        # Obtener resumen
        test_get_summary()

        # Actualizar
        test_update_dividend(div_id)

        # Verificar cambios
        test_get_dividends()

        # Eliminar
        test_delete_dividend(div_id)

        # Verificar eliminación
        test_get_dividends()

    print("\n" + "=" * 60)
    print("✅ Tests completados")
    print("=" * 60)
