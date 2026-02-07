# 💰 Feature: Tracking de Dividendos

## Resumen
Sistema completo para registrar y visualizar ingresos pasivos del portfolio (dividendos, cupones de bonos, staking rewards de criptomonedas).

---

## ✅ Implementado

### 1. **Modelo de Datos** - `models.py`
- ✅ Clase `Dividend` con campos:
  - `ticker`: Instrumento que genera el ingreso
  - `dividend_type`: dividend | coupon | staking
  - `payment_date`: Fecha de pago
  - `gross_amount`: Monto bruto (opcional)
  - `net_amount`: Monto neto recibido (requerido)
  - `shares_at_payment`: Acciones al momento del pago (auto-calculado)
  - `dividend_per_share`: Dividendo por acción (auto-calculado)
  - `notes`: Notas adicionales

### 2. **API Endpoints** - `app.py`

#### CRUD Básico:
- ✅ `GET /api/dividends` - Lista todos los dividendos (con filtros opcionales: ticker, type, year)
- ✅ `POST /api/dividends` - Crea nuevo dividendo
- ✅ `PUT /api/dividends/<id>` - Actualiza dividendo
- ✅ `DELETE /api/dividends/<id>` - Elimina dividendo

#### Reportes:
- ✅ `GET /api/dividends/summary?year=2024` - Resumen con:
  - Total recibido en el año
  - Dividend yield del portfolio
  - Desglose por tipo (dividend/coupon/staking)
  - Desglose por mes
  - Desglose por ticker
  - Contador de pagos

- ✅ `GET /api/dividends/expected-yield` - Yield esperado usando datos de yfinance:
  - Yield proyectado del portfolio
  - Dividendos esperados anuales por ticker
  - Nota: Solo referencia, puede variar por impuestos/FX

### 3. **Interfaz Web** - `templates/dividends.html`
- ✅ Dashboard con 4 KPI cards:
  - Total recibido (año actual)
  - Yield real del portfolio
  - Yield esperado (referencia)
  - Número de pagos registrados

- ✅ 3 Pestañas de análisis:
  - **Por Mes**: Gráfico de barras con evolución mensual
  - **Por Ticker**: Pie chart + tabla de distribución por activo
  - **Historial**: Tabla completa con opciones de editar/eliminar

- ✅ Modales:
  - Agregar dividendo (con auto-complete de tickers desde portfolio)
  - Editar dividendo

### 4. **JavaScript** - `static/js/dividends.js`
- ✅ Carga dinámica de datos
- ✅ Gráficos interactivos con Plotly
- ✅ CRUD completo desde UI
- ✅ Validación de formularios
- ✅ Notificaciones de éxito/error

### 5. **Navegación**
- ✅ Ruta `/dividends` agregada en `app.py`
- ✅ Link "Dividendos" en navbar principal

### 6. **Base de Datos**
- ✅ Tabla `dividends` creada automáticamente
- ✅ Función `load_sample_dividends()` para datos de ejemplo
  - Se activa con `LOAD_SAMPLE_DATA=true`
  - Incluye 6 dividendos de ejemplo (FUNO11.MX, VOO.MX, ETH, SOL)

---

## 🧪 Verificación

### Tests de API:
```bash
python3 test_dividends_api.py
```

**Resultados:**
✅ POST /api/dividends - Crear dividendo
✅ GET /api/dividends - Listar dividendos
✅ GET /api/dividends/summary - Resumen con yield
✅ PUT /api/dividends/<id> - Actualizar dividendo
✅ DELETE /api/dividends/<id> - Eliminar dividendo

### Esquema de Tabla:
```sql
CREATE TABLE dividends (
    id INTEGER PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    dividend_type VARCHAR(20) NOT NULL,
    payment_date DATE NOT NULL,
    gross_amount NUMERIC(15, 2),
    net_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3),
    shares_at_payment NUMERIC(15, 8),
    dividend_per_share NUMERIC(15, 6),
    notes TEXT,
    created_at DATETIME,
    updated_at DATETIME
);
```

---

## 📊 Características Destacadas

### Auto-cálculo Inteligente
Al crear un dividendo, el sistema:
1. Busca todas las transacciones del ticker hasta la fecha de pago
2. Calcula el total de acciones/unidades poseídas
3. Calcula automáticamente el dividendo por acción/unidad

### Soporte Multi-Tipo
- **Dividendos**: Acciones tradicionales (FUNO11.MX, VOO.MX, etc.)
- **Cupones**: Bonos gubernamentales, CETES, UDIBONOS
- **Staking**: Criptomonedas (ETH, SOL)

### Yield Real vs Esperado
- **Yield Real**: Calculado con dividendos realmente recibidos
- **Yield Esperado**: Obtenido de yfinance (solo referencia)

### Filtros Flexibles
- Por ticker: Ver solo dividendos de un activo
- Por tipo: Filtrar dividend/coupon/staking
- Por año: Análisis por periodo fiscal

---

## 🎯 Casos de Uso

### 1. Registro de Dividendo
```json
POST /api/dividends
{
  "ticker": "FUNO11.MX",
  "dividend_type": "dividend",
  "payment_date": "2024-03-15",
  "gross_amount": 180.00,
  "net_amount": 150.00,
  "notes": "Dividendo Q1 2024"
}
```

### 2. Análisis Anual
```
GET /api/dividends/summary?year=2024

Retorna:
- Total recibido: $1,234.56
- Yield: 3.45%
- Por mes, por ticker, por tipo
```

### 3. Proyección de Ingresos
```
GET /api/dividends/expected-yield

Retorna yield esperado por ticker usando datos públicos
```

---

## 🔄 Flujo de Trabajo

1. **Usuario agrega transacciones** (ya existente)
2. **Cuando recibe dividendo:**
   - Accede a `/dividends`
   - Click "Registrar Dividendo"
   - Selecciona ticker (auto-complete)
   - Ingresa fecha y monto neto
   - Sistema calcula dividendo por acción
3. **Visualización:**
   - Ve resumen anual
   - Analiza distribución por ticker/mes
   - Compara yield real vs esperado
4. **Editar/Eliminar** según necesidad

---

## 📝 Notas de Implementación

### Precisión Numérica
- Usa `Numeric` de SQLAlchemy para mantener precisión decimal
- Soporta hasta 8 decimales para crypto

### Manejo de Impuestos
- `gross_amount`: Opcional, antes de impuestos
- `net_amount`: Requerido, lo que realmente se recibió
- Útil para tracking fiscal

### Integración con Portfolio
- Calcula yield sobre valor real del portfolio
- Usa precios actuales de `get_current_price()`

---

## 🚀 Próximos Pasos Sugeridos

1. **Export a CSV/Excel** para análisis fiscal
2. **Notificaciones** de próximos dividendos esperados
3. **Comparación** con yield promedio del mercado
4. **Gráfico de tendencia** de yield a lo largo del tiempo
5. **Proyección** de ingresos para próximo año

---

## 📂 Archivos Modificados/Creados

### Creados:
- `models.py` → Clase Dividend
- `templates/dividends.html` → UI completa
- `static/js/dividends.js` → Lógica frontend
- `test_dividends_api.py` → Suite de tests

### Modificados:
- `app.py` → Endpoints CRUD + reportes + ruta
- `database.py` → load_sample_dividends()
- `templates/base.html` → Link en navbar

---

## ✅ Checklist de Deployment

- [x] Modelo creado
- [x] Tabla en base de datos
- [x] Endpoints implementados
- [x] Frontend funcional
- [x] Tests pasando
- [x] Navegación integrada
- [x] Datos de ejemplo disponibles
- [x] Documentación completa

---

**Estado:** ✅ **LISTO PARA PRODUCCIÓN**

El feature está completamente funcional y listo para uso. Para activar datos de ejemplo, configurar `LOAD_SAMPLE_DATA=true` en variables de entorno.
