# FinanceTracker

Portfolio tracker con análisis Swensen para acciones mexicanas, estadounidenses y criptomonedas.

## Características

### Core
- **Multi-activo**: Acciones MX (.MX), acciones US, y 5 criptomonedas (BTC, ETH, SOL, XRP, PAXG)
- **Precios en tiempo real**: Yahoo Finance para acciones, CryptoCompare para crypto
- **Conversión automática**: USD → MXN para consolidación
- **Sistema de custodios**: GBM, Bitso, Interactive Brokers, etc.

### Análisis Swensen
- **10 clases de activos**: Acciones MX, US, Internacionales, Emergentes, FIBRAs, CETES, Bonos, UDIBONOS, Oro, Crypto
- **Modelo personalizable**: Ajusta los porcentajes objetivo
- **Recomendaciones de rebalanceo**: Qué comprar para alcanzar tu modelo ideal
- **Calculadora de inversión**: Distribuye nuevos aportes según tu modelo

### Visualización
- **Dashboard interactivo**: KPIs, evolución temporal, distribución por clase
- **Gráficos Plotly**: Pie charts, líneas de evolución, comparativos
- **Selector de rango**: 1 año, 3 años, 5 años, todo el historial

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Backend | Python 3.11, Flask |
| Base de datos | SQLite |
| APIs | yfinance, CryptoCompare |
| Frontend | Bootstrap 5, Plotly.js |
| Deployment | Render.com |

## Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/osoberanes/FinanceTracker.git
cd FinanceTracker

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python app.py
```

Abrir http://localhost:5000

## Variables de Entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `CRYPTOCOMPARE_API_KEY` | API key de CryptoCompare | Sí (para crypto) |
| `LOAD_SAMPLE_DATA` | Cargar datos demo (`true`/`false`) | No |
| `PORT` | Puerto del servidor | No (default: 5000) |

## Estructura del Proyecto

```
FinanceTracker/
├── app.py                  # Flask app principal + endpoints API
├── models.py               # Modelos SQLAlchemy
├── database.py             # Inicialización BD + datos demo
├── utils.py                # Precios de acciones (yfinance)
├── utils_classification.py # Sistema Swensen (10 clases)
├── crypto_utils.py         # Precios crypto (CryptoCompare)
├── requirements.txt        # Dependencias Python
├── render.yaml             # Configuración Render.com
├── .python-version         # Python 3.11.9
├── static/
│   ├── css/style.css
│   └── js/main.js, settings.js, analysis.js
└── templates/
    ├── base.html
    ├── index.html          # Dashboard
    ├── settings.html       # Configuración
    └── analysis.html       # Análisis Swensen
```

## API Endpoints

### Transacciones
- `GET /api/transactions` - Listar todas
- `POST /api/transactions` - Crear nueva
- `DELETE /api/transactions/<id>` - Eliminar

### Portfolio
- `GET /api/portfolio/summary` - Resumen consolidado
- `GET /api/portfolio/history?range=1y|3y|5y|all` - Evolución temporal
- `GET /api/portfolio/by-custodian` - Agrupado por custodio
- `GET /api/portfolio/by-asset-class` - Agrupado por clase Swensen

### Análisis
- `GET /api/portfolio/rebalancing-recommendations` - Recomendaciones
- `POST /api/investment-calculator` - Calcular distribución de inversión

### Configuración
- `GET/POST /api/custodians` - Gestión de custodios
- `GET/POST /api/swensen-config` - Modelo Swensen personalizado
- `GET/POST /api/classifications` - Clasificación de activos

## Clases de Activos (Swensen)

| Clase | Emoji | Meta Default |
|-------|-------|--------------|
| Acciones México | 🇲🇽 | 15% |
| Acciones USA | 🇺🇸 | 30% |
| Acciones Internacionales | 🌍 | 15% |
| Mercados Emergentes | 🌎 | 5% |
| FIBRAs | 🏢 | 20% |
| CETES | 🏦 | 5% |
| Bonos Gubernamentales | 📜 | 5% |
| UDIBONOS | 🛡️ | 5% |
| Oro y Materias Primas | 🥇 | 0% |
| Criptomonedas | 🪙 | 0% |

## Deployment en Render

El proyecto está configurado para deploy automático en Render.com:

1. Conectar repositorio GitHub
2. Configurar variables de entorno:
   - `CRYPTOCOMPARE_API_KEY`
   - `LOAD_SAMPLE_DATA=true` (para demo)
3. Deploy automático en cada push a `main`

## Roadmap

- [ ] Sistema de ventas (registrar ventas de activos)
- [ ] Edición de transacciones
- [ ] Validación inteligente de decimales (enteros para acciones, decimales para crypto)
- [ ] Tracking de dividendos
- [ ] Comparación con benchmarks (IPC, S&P 500)
- [ ] Sistema de usuarios

## Licencia

MIT License

---

**Nota**: Los datos de precios son solo informativos. No constituyen asesoría financiera.
