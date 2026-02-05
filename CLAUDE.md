# FinanceTracker - Contexto para Claude

## Descripción del Proyecto
Portfolio tracker para inversiones con análisis basado en el modelo Swensen. Soporta acciones mexicanas (.MX), estadounidenses, y 5 criptomonedas (BTC, ETH, SOL, XRP, PAXG).

## Stack Tecnológico
- **Backend:** Python 3.11.9, Flask 3.0.0
- **Base de datos:** SQLite
- **APIs:** yfinance (acciones), CryptoCompare (crypto)
- **Frontend:** Bootstrap 5, Plotly.js
- **Deployment:** Render.com (Free tier)

## Estructura del Proyecto
```
FinanceTracker/
├── app.py                  # Flask app principal (~62K líneas) - endpoints API
├── models.py               # Modelos SQLAlchemy (Transaction, Custodian, SwensenConfig)
├── database.py             # Inicialización BD + datos demo
├── utils.py                # Precios de acciones (yfinance)
├── utils_classification.py # Sistema Swensen (10 clases de activos)
├── crypto_utils.py         # Precios crypto (CryptoCompare API)
├── requirements.txt        # Dependencias Python
├── render.yaml             # Configuración Render.com
├── .python-version         # Python 3.11.9 (crítico para compatibilidad)
├── static/
│   ├── css/style.css
│   └── js/
│       ├── main.js         # Dashboard logic
│       ├── settings.js     # Settings logic
│       └── analysis.js     # Análisis Swensen logic
└── templates/
    ├── base.html           # Template base + navbar
    ├── index.html          # Dashboard principal
    ├── settings.html       # Configuración (custodios, modelo Swensen)
    └── analysis.html       # Análisis Swensen
```

## Modelos de Datos

### Transaction
- `id`, `asset_type` ('stock'|'crypto'), `ticker`, `market` ('US'|'MX'|'CRYPTO')
- `transaction_type` ('buy'|'sell'), `asset_class` (clasificación Swensen)
- `purchase_date`, `purchase_price`, `quantity`, `custodian_id`, `currency`

### Custodian
- `id`, `name`, `type`, `is_active`

### SwensenConfig
- `id`, `asset_class`, `target_percentage`, `is_active`, `notes`

## 10 Clases de Activos (Swensen)
1. Acciones México (🇲🇽) - 15%
2. Acciones USA (🇺🇸) - 30%
3. Acciones Internacionales (🌍) - 15%
4. Mercados Emergentes (🌎) - 5%
5. FIBRAs (🏢) - 20%
6. CETES (🏦) - 5%
7. Bonos Gubernamentales (📜) - 5%
8. UDIBONOS (🛡️) - 5%
9. Oro y Materias Primas (🥇) - 0%
10. Criptomonedas (🪙) - 0%

## Variables de Entorno
| Variable | Descripción |
|----------|-------------|
| `CRYPTOCOMPARE_API_KEY` | API key para precios crypto (requerida) |
| `LOAD_SAMPLE_DATA` | `true`/`false` - cargar datos demo |
| `PORT` | Puerto del servidor (default: 5000) |

## Endpoints API Principales

### Transacciones
- `GET /api/transactions` - Listar todas
- `POST /api/transactions` - Crear (valida decimales: enteros para acciones, hasta 8 para crypto)
- `PUT /api/transactions/<id>` - Editar
- `DELETE /api/transactions/<id>` - Eliminar

### Portfolio
- `GET /api/portfolio/summary` - Resumen consolidado
- `GET /api/portfolio/history?range=1y|3y|5y|all` - Evolución temporal
- `GET /api/portfolio/by-custodian` - Por custodio
- `GET /api/portfolio/by-asset-class` - Por clase Swensen
- `GET /api/available-quantity/<ticker>` - Cantidad disponible para venta

### Configuración
- `GET/POST /api/custodians` - Gestión de custodios
- `GET/POST /api/swensen-config` - Modelo personalizado
- `GET/POST /api/classifications` - Clasificación de activos

## Reglas de Negocio Importantes

### Validación de Cantidad
- **Acciones:** Solo números enteros
- **Crypto:** Hasta 8 decimales

### Tickers Mexicanos
- Deben terminar en `.MX` (ej: `VOO.MX`, `FUNO11.MX`)
- El sistema auto-formatea si el usuario no lo incluye

### Ventas
- Valida que haya cantidad suficiente antes de permitir venta
- Calcula ganancias realizadas vs no realizadas

## Comandos de Desarrollo

```bash
# Desarrollo local
python app.py

# Con datos demo
LOAD_SAMPLE_DATA=true python app.py

# Deploy (automático al hacer push)
git push origin main
```

## Issues Conocidos
- Gráfico de evolución muestra frecuencia mensual (pendiente restaurar diario)

## Repositorio
https://github.com/osoberanes/FinanceTracker
