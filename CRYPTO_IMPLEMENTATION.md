# Implementación de Soporte para Criptomonedas

## Resumen

Se ha implementado soporte completo para criptomonedas en FinanceTracker. Esta implementación permite rastrear BTC, ETH, SOL, XRP y PAXG con precios en tiempo real desde CoinCap API y conversión automática a MXN.

## Criptomonedas Soportadas

- **BTC** (Bitcoin)
- **ETH** (Ethereum)
- **SOL** (Solana)
- **XRP** (Ripple)
- **PAXG** (Pax Gold)

## Cambios Implementados

### 1. Nuevo Módulo: crypto_utils.py

Archivo: `/home/oscar/claude/FinanceTracker/crypto_utils.py`

Funcionalidades:
- `get_crypto_price(symbol)` - Obtiene precio actual en MXN
- `get_crypto_historical_price(symbol, date)` - Obtiene precio histórico en MXN
- `is_crypto(ticker)` - Determina si un ticker es criptomoneda
- `validate_crypto_symbol(symbol)` - Valida si una crypto es soportada
- Caché de precios (5 minutos)
- Uso de CoinCap API (sin API key requerida)
- Conversión automática USD → MXN usando Yahoo Finance

### 2. Modificaciones en utils.py

Archivo: `/home/oscar/claude/FinanceTracker/utils.py`

Cambios:
- Importación de funciones de crypto_utils
- `get_current_price()` ahora detecta y maneja cryptos
- `get_historical_prices()` implementa fetching diario para cryptos
- `validate_ticker()` valida tanto stocks como cryptos

### 3. Modificaciones en models.py

Archivo: `/home/oscar/claude/FinanceTracker/models.py`

Cambios:
- Método `to_dict()` ahora formatea cantidades con 8 decimales para cryptos
- Mantiene 2 decimales para stocks

### 4. Modificaciones en templates/index.html

Archivo: `/home/oscar/claude/FinanceTracker/templates/index.html`

Cambios:
- Selector de mercado incluye opción "🪙 Criptomonedas"
- Input de cantidad soporta hasta 8 decimales (step="0.00000001")
- Hints dinámicos según el mercado seleccionado
- Modal de edición también soporta cryptos

### 5. Modificaciones en static/js/main.js

Archivo: `/home/oscar/claude/FinanceTracker/static/js/main.js`

Cambios:
- Constante `SUPPORTED_CRYPTOS` con lista de cryptos soportadas
- Función `isCrypto(ticker)` para detectar cryptos
- Función `formatQuantity(quantity, ticker)` con formato inteligente
- Badges con emoji 🪙 para cryptos en tablas
- Hints dinámicos en selector de mercado

### 6. Modificaciones en app.py

Archivo: `/home/oscar/claude/FinanceTracker/app.py`

Cambios:
- Importación de `is_crypto` desde crypto_utils
- Endpoint POST `/api/transactions`:
  - Detecta market='CRYPTO'
  - No agrega sufijos .MX para cryptos
  - Valida cryptos con crypto_utils
  - Asigna asset_type='crypto'
- Endpoint PUT `/api/transactions/<id>`:
  - Misma lógica de detección y validación
  - Actualiza asset_type correctamente

## Flujo de Funcionamiento

### Agregar Transacción de Crypto

1. Usuario selecciona "🪙 Criptomonedas" en el selector de mercado
2. Ingresa símbolo (ej: BTC)
3. Ingresa cantidad con hasta 8 decimales (ej: 0.05234567)
4. Ingresa precio de compra en MXN
5. Frontend envía `market: 'CRYPTO'` al backend
6. Backend:
   - Detecta que es crypto
   - No agrega sufijo .MX
   - Valida con `validate_crypto_symbol()`
   - Crea transacción con `asset_type='crypto'`

### Visualización de Precios

1. Al cargar dashboard, se llama `get_current_price(ticker)` para cada transacción
2. Si `is_crypto(ticker)` retorna true:
   - Llama a `get_crypto_price(ticker)` en crypto_utils
   - Obtiene precio USD desde CoinCap API
   - Obtiene tipo de cambio USD/MXN desde Yahoo Finance
   - Retorna precio en MXN
3. Si es stock:
   - Proceso normal con Yahoo Finance

### Formateo de Cantidades

- **Cryptos**: Se muestran con 8 decimales (ej: 0.05234567 BTC)
- **Stocks**: Se muestran con 4 decimales (ej: 10.5000 AAPL)

## Estructura de Datos

### Transaction Model

```python
Transaction(
    id=1,
    ticker='BTC',
    asset_type='crypto',  # Nuevo campo
    market='CRYPTO',
    purchase_price=850000.00,  # En MXN
    quantity=0.05234567,  # Hasta 8 decimales
    currency='MXN'
)
```

## APIs Utilizadas

### CoinCap API v2
- **Base URL**: https://api.coincap.io/v2
- **Endpoint actual**: `/assets/{asset_id}`
- **Endpoint histórico**: `/assets/{asset_id}/history?interval=d1&start={ms}&end={ms}`
- **No requiere API key**
- **Rate limit**: Generoso para uso personal

### Yahoo Finance (USD/MXN)
- **Ticker**: USDMXN=X
- **Biblioteca**: yfinance
- **Usado para**: Tipo de cambio USD/MXN

## Caché

- Precios actuales: 5 minutos
- Tipo de cambio: 5 minutos
- Mejora rendimiento y reduce llamadas API

## Ejemplo de Uso

```python
# Obtener precio actual de Bitcoin en MXN
from crypto_utils import get_crypto_price
precio_btc = get_crypto_price('BTC')
# Retorna: 1750000.00 (MXN)

# Obtener precio histórico
precio_btc_historico = get_crypto_historical_price('BTC', '2024-01-01')
# Retorna: 850000.00 (MXN)

# Validar símbolo
from crypto_utils import validate_crypto_symbol
es_valido = validate_crypto_symbol('BTC')  # True
es_valido = validate_crypto_symbol('DOGE')  # False
```

## Pruebas

Para probar la implementación:

```bash
# Probar módulo crypto_utils
cd /home/oscar/claude/FinanceTracker
python3 crypto_utils.py

# Iniciar aplicación
python3 app.py
```

Luego:
1. Ir a http://localhost:5000
2. Seleccionar "🪙 Criptomonedas" en mercado
3. Ingresar BTC como ticker
4. Ingresar cantidad (ej: 0.00123456)
5. Ingresar precio en MXN
6. Agregar transacción
7. Ver portfolio actualizado con precio actual de BTC

## Limitaciones Actuales

1. **Cryptos soportadas**: Solo 5 cryptos (BTC, ETH, SOL, XRP, PAXG)
2. **Históricos**: CoinCap API limita a datos diarios
3. **Staking**: No implementado aún (preparado en el plan original)

## Extensiones Futuras

1. **Más cryptos**: Agregar más símbolos a `CRYPTO_COINCAP_IDS`
2. **Staking rewards**: Agregar campo para ETH y SOL staking
3. **DeFi**: Soporte para posiciones en DeFi
4. **Exchanges**: Tracking por exchange (Binance, Coinbase, etc.)
5. **Tax reporting**: Cálculo de ganancias para impuestos

## Archivos Modificados

1. ✅ `/home/oscar/claude/FinanceTracker/crypto_utils.py` (NUEVO)
2. ✅ `/home/oscar/claude/FinanceTracker/utils.py`
3. ✅ `/home/oscar/claude/FinanceTracker/models.py`
4. ✅ `/home/oscar/claude/FinanceTracker/templates/index.html`
5. ✅ `/home/oscar/claude/FinanceTracker/static/js/main.js`
6. ✅ `/home/oscar/claude/FinanceTracker/app.py`

## Status de Implementación

✅ **COMPLETADO** - Todas las partes del plan han sido implementadas:

- [x] Parte 1: crypto_utils.py
- [x] Parte 2: Modificaciones en utils.py
- [x] Parte 3: Modificaciones en models.py
- [x] Parte 4: Modificaciones en templates/index.html
- [x] Parte 5: Modificaciones en static/js/main.js
- [x] Parte 6: Modificaciones en app.py
- [x] Parte 7: Documentación

## Notas Técnicas

- Los precios de cryptos se almacenan en MXN en la base de datos
- La conversión USD→MXN se hace en tiempo real al obtener precios
- El caché reduce la carga en las APIs externas
- La base de datos SQLite maneja sin problemas los 8 decimales (tipo Float)
- Frontend valida formato antes de enviar al backend
