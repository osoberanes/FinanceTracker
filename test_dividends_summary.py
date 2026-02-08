#!/usr/bin/env python3
"""Script para probar el endpoint de summary"""

import requests
import json

url = "http://localhost:5000/api/dividends/summary?year=2024"

try:
    response = requests.get(url)
    print(f"Status: {response.status_code}\n")

    if response.ok:
        data = response.json()
        print("SUMMARY DATA:")
        print(json.dumps(data, indent=2))
        print(f"\n✅ Total confirmados: {data['count']}")
        print(f"✅ Total dividends: ${data['total_dividends']}")
        print(f"✅ Pendientes: {data['pending_count']}")
        print(f"\n📅 Por mes: {data['by_month']}")
        print(f"📊 Por ticker: {data['by_ticker']}")
    else:
        print(f"❌ Error: {response.text}")

except Exception as e:
    print(f"❌ Error de conexión: {e}")
    print("\n⚠️ Asegúrate de que la app esté corriendo con:")
    print("   python3 app.py")
