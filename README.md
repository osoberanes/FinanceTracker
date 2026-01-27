# Portfolio Tracker

Una aplicación web para seguimiento de cartera de inversiones en acciones con análisis en tiempo real, visualización de evolución temporal y consolidación de posiciones.

## Características

- **Ingreso de Transacciones**: Formulario para agregar compras de acciones con validación en tiempo real
- **Histórico de Transacciones**: Tabla detallada con todas las transacciones y valores actuales
- **Posiciones Consolidadas**: Agrupación automática por ticker con precio promedio ponderado
- **Gráfico de Evolución**: Visualización interactiva del crecimiento de la cartera en el tiempo
- **KPIs en Tiempo Real**: Métricas clave como total invertido, valor actual, ganancias/pérdidas
- **Actualización Automática**: Precios de acciones actualizados desde Yahoo Finance

## Stack Tecnológico

- **Backend**: Python 3.9+, Flask, SQLAlchemy
- **Base de Datos**: SQLite
- **APIs Externas**: yfinance (Yahoo Finance)
- **Análisis de Datos**: Pandas
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **UI Framework**: Bootstrap 5
- **Gráficos**: Plotly.js

## Requisitos Previos

- Python 3.9 o superior
- pip (gestor de paquetes de Python)

## Instalación

1. **Clonar o navegar al directorio del proyecto**
   ```bash
   cd FinanceTracker
   ```

2. **Crear un entorno virtual (recomendado)**
   ```bash
   python -m venv venv

   # En Linux/Mac
   source venv/bin/activate

   # En Windows
   venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución

1. **Iniciar la aplicación**
   ```bash
   python app.py
   ```

2. **Abrir navegador**
   ```
   http://localhost:5000
   ```

3. **Detener el servidor**
   ```
   Presionar CTRL+C en la terminal
   ```

## Primera Vez

- La base de datos SQLite (`portfolio.db`) se crea automáticamente al iniciar la aplicación
- No se requiere configuración adicional
- Comenzar agregando transacciones mediante el formulario

## Uso

### Agregar una Transacción

1. Completar el formulario en la parte superior:
   - **Ticker**: Símbolo de la acción (ej: AAPL, MSFT, GOOGL)
   - **Fecha de Compra**: Fecha de la operación (no puede ser futura)
   - **Precio de Compra**: Precio unitario pagado
   - **Cantidad**: Número de acciones compradas

2. Hacer clic en "Agregar"

3. El sistema validará que el ticker exista en Yahoo Finance antes de guardar

### Visualizar el Dashboard

- **KPIs**: Resumen general en la parte superior
- **Gráfico**: Evolución del valor de la cartera desde la primera compra
- **Posiciones Consolidadas**: Vista agrupada por ticker con métricas consolidadas
- **Histórico**: Todas las transacciones con valores actuales

### Interpretación de Colores

- **Verde**: Ganancias positivas
- **Rojo**: Pérdidas
- **Gris**: Sin datos disponibles

## Estructura del Proyecto

```
FinanceTracker/
├── app.py                 # Aplicación Flask principal con rutas y API
├── models.py              # Modelos SQLAlchemy (tabla transactions)
├── database.py            # Configuración y conexión a SQLite
├── utils.py               # Funciones auxiliares (precios, cálculos)
├── requirements.txt       # Dependencias Python
├── portfolio.db           # Base de datos SQLite (se crea automáticamente)
├── README.md              # Este archivo
├── static/
│   ├── css/
│   │   └── style.css     # Estilos personalizados
│   └── js/
│       └── main.js       # Lógica frontend (AJAX, gráficos, tablas)
└── templates/
    ├── base.html         # Template base con navbar y estructura
    └── index.html        # Dashboard principal
```

## API Endpoints

La aplicación expone los siguientes endpoints REST:

- `GET /` - Dashboard principal (HTML)
- `GET /api/transactions` - Obtener todas las transacciones con datos enriquecidos
- `POST /api/transactions` - Crear nueva transacción
- `GET /api/portfolio/summary` - Resumen consolidado por ticker
- `GET /api/portfolio/history` - Datos históricos para el gráfico

## Funcionalidades Futuras (Preparadas en BD)

La base de datos está diseñada para futuras extensiones:

- Múltiples tipos de activos (crypto, CETES, bonos)
- Soporte multi-moneda (USD, MXN)
- Registro de custodios (GBM, Binance, etc.)
- Comisiones por transacción
- Notas personalizadas
- Edición y eliminación de transacciones
- Registro de ventas

## Notas Técnicas

### Caché de Precios

- Los precios actuales se cachean por 5 minutos para reducir llamadas a la API
- Los precios históricos se cachean durante toda la sesión

### Rate Limiting

- Yahoo Finance tiene límites de ~2000 requests/hora
- El caché mitiga este límite

### Rendimiento del Gráfico

- Para rangos mayores a 6 meses, se muestrea semanalmente
- Optimiza tiempos de carga sin perder fidelidad visual

### Validaciones

- Ticker debe existir en Yahoo Finance
- Fechas no pueden ser futuras
- Precios y cantidades deben ser positivos
- Todos los campos son obligatorios

## Solución de Problemas

### Error: "Invalid ticker"

- Verificar que el símbolo sea correcto (ej: AAPL no APL)
- Algunos tickers requieren sufijos (ej: BRK.B para Berkshire Hathaway)

### Error: "No data returned"

- El ticker puede estar delisted o suspendido
- Verificar conectividad a internet

### El gráfico no se muestra

- Asegurarse de tener al menos una transacción
- Verificar consola del navegador para errores JavaScript

### Precios no se actualizan

- Yahoo Finance puede tener delays de ~15 minutos
- Mercados cerrados muestran último precio de cierre

## Contribuciones

Este proyecto es de código abierto. Sugerencias y mejoras son bienvenidas.

## Licencia

MIT License

## Autor

Desarrollado con Flask, Python y las mejores prácticas de desarrollo web.

---

**Nota**: Esta aplicación utiliza datos de Yahoo Finance mediante la librería yfinance. Los datos son solo para fines informativos y no constituyen asesoría financiera.
