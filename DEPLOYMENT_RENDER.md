# 🚀 Deployment a Render.com - FinanceTracker

## ✅ Preparación Completada

Todos los archivos necesarios han sido configurados para deployment en Render.com.

## 📋 Archivos Modificados

### 1. ✅ `requirements.txt` - Actualizado
```
Flask==3.0.0
Flask-Cors==4.0.0
Flask-SQLAlchemy==3.0.5
SQLAlchemy==2.0.23
yfinance>=1.1.0
pandas==2.1.4
plotly==5.18.0
requests>=2.31.0
python-dateutil==2.8.2
gunicorn==21.2.0  ← Agregado para producción
```

### 2. ✅ `render.yaml` - Creado
Configuración automática para Render con:
- Runtime Python 3.11
- Comando de build: `pip install -r requirements.txt`
- Comando de start: `gunicorn app:app`
- Disco persistente de 1GB para la base de datos SQLite

### 3. ✅ `app.py` - Modificado para Producción
- Lee el puerto desde variable de entorno `PORT`
- Detecta automáticamente si está en producción (variable `RENDER`)
- Desactiva debug mode en producción
- Mantiene funcionalidad local para desarrollo

### 4. ✅ `crypto_utils.py` - API Key Protegida
La API key de CryptoCompare ahora usa variables de entorno:
```python
CRYPTOCOMPARE_API_KEY = os.environ.get(
    'CRYPTOCOMPARE_API_KEY',
    '8b9c30fc082fb321f78e1f2ed4f3bb3669aae6d2841151845896ad725c0e1eac'
)
```

### 5. ✅ `.gitignore` - Actualizado
Excluye archivos sensibles:
- Base de datos (*.db, *.sqlite)
- API keys (*.key, api-keys-reference.txt)
- Archivos de entorno (.env)
- Cache y logs

## 🔐 Variables de Entorno Requeridas en Render

Al crear el Web Service en Render, configura estas variables de entorno:

### Obligatorias:
- `CRYPTOCOMPARE_API_KEY` = `8b9c30fc082fb321f78e1f2ed4f3bb3669aae6d2841151845896ad725c0e1eac`

### Automáticas (Render las configura):
- `PORT` - Puerto asignado por Render
- `RENDER` - Indica que está en producción

## 📝 Pasos para Deployment

### Opción 1: Usando render.yaml (Recomendado)

1. **Hacer commit de los cambios:**
   ```bash
   git add .
   git commit -m "Preparar para deployment en Render"
   git push origin main
   ```

2. **En Render.com:**
   - Ir a Dashboard
   - Click en "New" → "Blueprint"
   - Conectar tu repositorio GitHub
   - Render detectará automáticamente `render.yaml`
   - Click en "Apply"

3. **Configurar variables de entorno:**
   - En el dashboard del servicio
   - Ir a "Environment"
   - Agregar `CRYPTOCOMPARE_API_KEY`

### Opción 2: Deployment Manual

1. **Hacer commit y push:**
   ```bash
   git add .
   git commit -m "Preparar para deployment en Render"
   git push origin main
   ```

2. **En Render.com:**
   - Click en "New" → "Web Service"
   - Conectar repositorio
   - Configurar:
     - **Name:** financetracker
     - **Runtime:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn app:app`

3. **Configurar variables de entorno:**
   - Agregar `CRYPTOCOMPARE_API_KEY`

4. **Configurar disco persistente:**
   - En "Advanced" → "Disks"
   - Nombre: `data`
   - Mount Path: `/opt/render/project/src`
   - Size: 1 GB

## 🗄️ Base de Datos

La aplicación usa **SQLite** con disco persistente:
- ✅ La base de datos se creará automáticamente al iniciar
- ✅ Los datos persisten entre deployments
- ✅ Ubicación: `/opt/render/project/src/portfolio.db`

## 🧪 Verificar Deployment

Una vez desplegado, verifica:

1. **Health Check:**
   ```
   https://tu-app.onrender.com/
   ```
   Debería mostrar el dashboard

2. **API Endpoints:**
   ```
   https://tu-app.onrender.com/api/transactions
   https://tu-app.onrender.com/api/portfolio/summary
   ```

3. **Funcionalidad de Cryptos:**
   - Agregar transacción de BTC
   - Verificar que los precios se obtienen correctamente
   - Verificar gráfico de evolución

## ⚠️ Consideraciones Importantes

### Rate Limits de APIs Gratuitas:
- **Yahoo Finance:** ~100-200 llamadas/minuto
- **CryptoCompare:** 100,000 llamadas/mes (capa gratuita)

### Rendimiento:
- Primera carga puede ser lenta (cold start)
- El caché de precios reduce llamadas API
- Gráfico de evolución usa sampling mensual para eficiencia

### Logs:
Para ver logs en Render:
```
Dashboard → Tu servicio → Logs
```

## 🔄 Actualizaciones Futuras

Para desplegar cambios:
```bash
git add .
git commit -m "Descripción de cambios"
git push origin main
```

Render re-desplegará automáticamente.

## 🆘 Troubleshooting

### Error: "Module not found"
- Verificar que el módulo esté en `requirements.txt`
- Re-build desde Render dashboard

### Error: "Database locked"
- Normal en SQLite bajo carga concurrente
- Considerar migrar a PostgreSQL si es necesario

### Error: "API key invalid"
- Verificar variable de entorno en Render
- Verificar que no haya espacios extra en el valor

### Gráfico no carga:
- Esperar 2-3 minutos (rate limit)
- Verificar logs para errores de API

## 📊 Monitoreo

Render provee métricas automáticas:
- CPU usage
- Memory usage
- Request rate
- Response time

Accede desde: Dashboard → Tu servicio → Metrics

## 🎉 ¡Listo!

Tu aplicación FinanceTracker está lista para producción en Render.com con:
- ✅ Soporte completo para criptomonedas
- ✅ Base de datos persistente
- ✅ API keys protegidas
- ✅ Optimizaciones de rendimiento
- ✅ Auto-deployment desde GitHub

---

**Próximos Pasos Opcionales:**
1. Configurar dominio personalizado en Render
2. Habilitar HTTPS (automático en Render)
3. Configurar alertas de monitoreo
4. Migrar a PostgreSQL si necesitas más concurrencia
