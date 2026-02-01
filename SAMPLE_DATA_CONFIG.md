# 📊 Configuración de Datos de Ejemplo

## ✅ Implementación Completada

Se ha implementado un sistema para cargar datos de ejemplo controlado por variable de entorno.

## 🎯 Funcionamiento

### Variable de Control: `LOAD_SAMPLE_DATA`

```bash
# PRODUCCIÓN (default) - Base de datos vacía
# No configurar la variable o LOAD_SAMPLE_DATA=false

# DEMO/TESTING - Carga 13 transacciones de ejemplo
export LOAD_SAMPLE_DATA=true
```

## 📝 Datos de Ejemplo Incluidos

### Total: 13 Transacciones

**Distribución:**
- ✅ 7 Stocks (acciones mexicanas)
- ✅ 6 Cryptos (BTC, ETH, SOL, XRP, PAXG)
- ✅ 3 con staking (ETH x2, SOL x1)
- ✅ 13 con custodio asignado

### Detalles de las Transacciones:

| Fecha       | Ticker           | Cantidad    | Precio Compra | Asset Class              | Custodio |
|-------------|------------------|-------------|---------------|--------------------------|----------|
| 26/11/2025  | NVONLMX         | 5.00000000  | $895.94       | acciones_mexico          | GBM      |
| 29/09/2025  | PAXG            | 0.05000000  | $70,000.00    | oro_materias_primas      | Bitso    |
| 15/08/2025  | VWOMX           | 15.00000000 | $976.00       | acciones_mexico          | GBM      |
| 15/08/2025  | SOL             | 0.06360000  | $3,522.84     | criptomonedas (staking)  | Bitso    |
| 29/05/2025  | IAU.MX          | 12.00000000 | $1,208.00     | oro_materias_primas      | GBM      |
| 27/05/2025  | ETH             | 0.00580000  | $52,103.75    | criptomonedas (staking)  | Bitso    |
| 12/05/2025  | XRP             | 13.17000000 | $52.38        | criptomonedas            | Bitso    |
| 01/02/2025  | ETH             | 0.00250000  | $45,000.00    | criptomonedas (staking)  | Bitso    |
| 08/03/2024  | AGUILASCPO.MX   | 30.00000000 | $27.07        | acciones_mexico          | GBM      |
| 13/07/2023  | FUNO11MX        | 199.00000000| $25.00        | fibras                   | GBM      |
| 21/06/2023  | VOO.MX          | 3.00000000  | $6,955.95     | acciones_internacionales | GBM      |
| 31/05/2023  | VOO.MX          | 1.00000000  | $6,800.00     | acciones_internacionales | GBM      |
| 25/04/2023  | BTC             | 0.00400000  | $502,344.69   | criptomonedas            | Bitso    |

## 🔧 Modificaciones Realizadas

### 1. Archivo: `database.py`

#### Nueva función: `load_sample_data()`

**Ubicación:** Al final del archivo, antes del bloque `if __name__`

**Características:**
- ✅ Lee variable de entorno `LOAD_SAMPLE_DATA`
- ✅ Solo carga si `LOAD_SAMPLE_DATA=true`
- ✅ Verifica que la base de datos esté vacía
- ✅ Carga 13 transacciones con clasificación automática
- ✅ Asigna custodios (GBM para stocks, Bitso para cryptos)
- ✅ Marca ETH y SOL con `generates_staking=True`
- ✅ Manejo de errores por transacción individual

#### Modificación: `init_db()`

**Cambio realizado:**
```python
def init_db():
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(bind=engine)
    migrate_add_market_column()
    migrate_add_custodians()
    migrate_add_custodian_id_column()
    migrate_add_crypto_fields()
    migrate_add_asset_class_column()
    migrate_add_swensen_config()
    print(f"Database initialized at: {DATABASE_PATH}")

    # Intentar cargar datos de ejemplo (solo si LOAD_SAMPLE_DATA=true)
    load_sample_data()  # ← LÍNEA AGREGADA
```

## 🧪 Verificaciones Realizadas

### Test 1: Sin variable (PRODUCCIÓN) ✅
```bash
$ python3 -c "from database import init_db; init_db()"
Database initialized at: /home/oscar/claude/FinanceTracker/portfolio.db
ℹ️  LOAD_SAMPLE_DATA no está activado, saltando datos de ejemplo
```
**Resultado:** Base de datos vacía

### Test 2: Con variable (DEMO) ✅
```bash
$ LOAD_SAMPLE_DATA=true python3 -c "from database import init_db; init_db()"
Database initialized at: /home/oscar/claude/FinanceTracker/portfolio.db
📊 Cargando datos de ejemplo (LOAD_SAMPLE_DATA=true)...
✅ 13 transacciones de ejemplo cargadas exitosamente
```
**Resultado:** 13 transacciones cargadas

### Test 3: Prevención de duplicados ✅
```bash
$ LOAD_SAMPLE_DATA=true python3 -c "from database import init_db; init_db()"
Database initialized at: /home/oscar/claude/FinanceTracker/portfolio.db
ℹ️  Base de datos ya tiene datos, saltando carga de ejemplos
```
**Resultado:** No duplica datos si ya existen

## 🚀 Uso en Render.com

### Para Demo/Testing:

Agregar variable de entorno en Render:

```
Key: LOAD_SAMPLE_DATA
Value: true
```

**Resultado:** Al desplegar, la app cargará automáticamente las 13 transacciones de ejemplo.

### Para Producción:

**Opción 1 (Recomendada):** No configurar la variable
**Opción 2:** Configurar como `LOAD_SAMPLE_DATA=false`

**Resultado:** Base de datos inicia vacía, el usuario agrega sus propias transacciones.

## 📋 Comportamiento por Caso

| Escenario | LOAD_SAMPLE_DATA | DB Vacía | Resultado |
|-----------|------------------|----------|-----------|
| Producción limpia | no configurada | Sí | No carga datos ✅ |
| Producción limpia | false | Sí | No carga datos ✅ |
| Demo limpio | true | Sí | Carga 13 transacciones ✅ |
| Demo con datos | true | No | No duplica datos ✅ |
| Producción con datos | true | No | No afecta datos existentes ✅ |

## 🛠️ Desarrollo Local

### Probar con datos de ejemplo:
```bash
# Eliminar DB existente
rm portfolio.db

# Inicializar con datos de ejemplo
LOAD_SAMPLE_DATA=true python3 database.py

# Verificar
python3 verify_sample_data.py
```

### Probar sin datos de ejemplo:
```bash
# Eliminar DB existente
rm portfolio.db

# Inicializar vacía
python3 database.py

# Verificar
python3 verify_sample_data.py
```

## 📊 Script de Verificación

Se creó `verify_sample_data.py` para verificar los datos cargados:

```bash
$ python3 verify_sample_data.py

📊 TRANSACCIONES CARGADAS: 13
...
✅ Stocks: 7
✅ Cryptos: 6
✅ Con staking: 3
✅ Con custodio asignado: 13
```

## 🔐 Seguridad

✅ **No afecta datos de producción:**
- Si la DB tiene datos, no hace nada
- Variable de entorno debe ser explícitamente `true`
- Default es NO cargar datos

✅ **Fácil de controlar:**
- Una sola variable de entorno
- Comportamiento predecible
- Logs claros sobre qué está pasando

## 📝 Logs Informativos

La función muestra mensajes claros:

```
ℹ️  LOAD_SAMPLE_DATA no está activado, saltando datos de ejemplo
```
→ Variable no configurada o =false

```
📊 Cargando datos de ejemplo (LOAD_SAMPLE_DATA=true)...
✅ 13 transacciones de ejemplo cargadas exitosamente
```
→ Datos cargados correctamente

```
ℹ️  Base de datos ya tiene datos, saltando carga de ejemplos
```
→ DB no está vacía, no duplica

```
⚠️  Custodios no encontrados, creando transacciones sin custodio
```
→ Warning si falta tabla de custodios

```
⚠️  Error creando transacción BTC: [error]
```
→ Error en transacción específica (continúa con las demás)

## 🎯 Próximos Pasos

### Para desplegar demo en Render:

1. **Ir al dashboard de Render**
2. **Environment → Add Environment Variable**
3. **Agregar:**
   ```
   LOAD_SAMPLE_DATA=true
   ```
4. **Re-deploy**
5. **Verificar:** La app tendrá 13 transacciones precargadas

### Para desplegar producción en Render:

1. **NO configurar `LOAD_SAMPLE_DATA`**
2. **Deploy**
3. **Verificar:** La app inicia con base de datos vacía

---

**Implementado:** 2026-01-29
**Versión:** 1.0
**Estado:** ✅ Completado y verificado
