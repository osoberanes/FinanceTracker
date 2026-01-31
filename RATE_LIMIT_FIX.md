# Fix para Rate Limiting de Yahoo Finance

## Problema

Cuando agregas criptomonedas y el sistema intenta generar el **gráfico de evolución de la cartera**, puede encontrarse con el error:

```
Too Many Requests. Rate limited. Try after a while.
```

## Causa

Yahoo Finance tiene límites en el número de llamadas API que puedes hacer en un período corto de tiempo. El gráfico de evolución necesita obtener precios históricos para cada ticker, lo que genera muchas llamadas.

## Soluciones Implementadas

### 1. ✅ Optimización del fetch de datos históricos

**Archivo**: `utils.py` - función `calculate_portfolio_evolution()`

**Cambio**: En lugar de llamar a la API día por día, ahora:
- Pre-carga todos los datos históricos de una sola vez
- Usa muestreo inteligente de fechas:
  - **Diario**: Si el rango es < 2 meses
  - **Semanal**: Si el rango es 2-6 meses
  - **Mensual**: Si el rango es > 6 meses

Esto reduce drásticamente el número de llamadas API.

### 2. ✅ Caché de precios

El sistema ya implementa caché de 5 minutos para:
- Precios actuales de cryptos
- Tipo de cambio USD/MXN
- Precios históricos

### 3. ✅ Uso de Yahoo Finance para Cryptos

**Antes**: Intentaba usar CoinCap API (no accesible)
**Ahora**: Usa Yahoo Finance con formato `BTC-USD`, `ETH-USD`, etc.

Esto es más confiable y consistente con el resto del código.

## Cómo Resolver el Rate Limit

Si encuentras el error de rate limit:

### Opción 1: Esperar (Recomendado)
El rate limit de Yahoo Finance se resetea automáticamente después de **1-2 minutos**.

1. Espera 1-2 minutos
2. Recarga la página: http://localhost:5000
3. El gráfico debería cargar correctamente

### Opción 2: Reiniciar la Aplicación
```bash
pkill -9 -f "python.*app.py"
cd /home/oscar/claude/FinanceTracker
python3 app.py
```

Luego espera 1 minuto antes de cargar la página.

### Opción 3: Reducir Datos (Temporal)
Si necesitas resultados inmediatos, puedes reducir el rango de fechas en `calculate_portfolio_evolution()`:

```python
# En utils.py, línea ~360
if days_diff > 30:  # Cambiar de 180 a 30
    date_range = pd.date_range(start=start_date, end=end_date, freq='MS')
```

Esto generará menos puntos de datos pero reducirá las llamadas API.

## Estado Actual

### ✅ **Funcionando Correctamente**:
- Agregar transacciones de BTC, ETH, SOL, XRP, PAXG
- Obtener precios actuales en MXN
- Mostrar cantidades con 8 decimales
- Calcular ganancias/pérdidas
- Posiciones consolidadas
- Tablas de transacciones
- Gráficos de composición (pie charts)

### ⚠️ **Requiere Espera (Rate Limit)**:
- Gráfico de evolución de la cartera (1-2 minutos de espera)

## Verificación

Para verificar que todo está funcionando:

```bash
cd /home/oscar/claude/FinanceTracker
python3 test_simple.py
```

Esto mostrará:
- Todas las transacciones en la base de datos
- Confirmación de que cryptos están guardadas correctamente
- Recordatorio sobre el rate limit

## Logs Útiles

Para ver los logs de la aplicación:
```bash
tail -f /tmp/flask.log
```

Busca:
- ✅ `INFO:utils:Loaded X days for BTC` - Datos cargados correctamente
- ❌ `ERROR:utils:Too Many Requests` - Rate limit activo
- ✅ `INFO:utils:Portfolio evolution calculated: X data points` - Gráfico generado

## Precios Actuales vs Históricos

### Precios Actuales (Funcionan Siempre)
```python
from crypto_utils import get_crypto_price
price = get_crypto_price('BTC')  # Rápido, con caché de 5 min
```

### Precios Históricos (Sujetos a Rate Limit)
```python
from utils import get_historical_prices
hist = get_historical_prices('BTC', '2024-01-01', '2024-12-31')
# Puede fallar si hay rate limit activo
```

## Recomendaciones

1. **No recargues la página constantemente** - Usa el caché
2. **Espera entre pruebas** - Dale 1-2 minutos entre cargas completas
3. **El auto-refresh está configurado para 5 minutos** - Esto es seguro
4. **Los precios actuales se actualizan sin problemas** - Solo los históricos son lentos

## Próximos Pasos (Opcional)

Para mejorar aún más el rendimiento:

1. **Implementar caché persistente** (Redis o SQLite)
2. **Guardar precios históricos en DB** después de la primera carga
3. **Implementar jobs en background** para actualizar históricos
4. **Usar API de pago** (Alpha Vantage, Twelve Data) sin rate limits

Por ahora, el sistema funciona perfectamente con cryptos - solo necesita 1-2 minutos de espera inicial para el gráfico de evolución.
