# ✅ Checklist de Deployment - Render.com

## Pre-Deployment (Completado)

- [x] requirements.txt actualizado con gunicorn
- [x] render.yaml creado
- [x] app.py configurado para producción
- [x] API key protegida con variables de entorno
- [x] .gitignore actualizado
- [x] Estructura del proyecto verificada

## Git (Por hacer manualmente)

- [ ] Hacer commit de cambios:
  ```bash
  git add .
  git commit -m "Preparar para deployment en Render"
  git push origin main
  ```

## En Render.com (Por hacer)

### Opción A: Blueprint (Recomendado)
- [ ] Ir a https://dashboard.render.com
- [ ] Click "New" → "Blueprint"
- [ ] Conectar repositorio GitHub: `osoberanes/FinanceTracker`
- [ ] Render detectará automáticamente `render.yaml`
- [ ] Click "Apply"

### Opción B: Manual
- [ ] Click "New" → "Web Service"
- [ ] Conectar repositorio
- [ ] Name: `financetracker`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `gunicorn app:app`
- [ ] Add Disk: name=`data`, path=`/opt/render/project/src`, size=`1GB`

## Variables de Entorno

- [ ] En dashboard del servicio → "Environment"
- [ ] Add Variable:
  - Key: `CRYPTOCOMPARE_API_KEY`
  - Value: `8b9c30fc082fb321f78e1f2ed4f3bb3669aae6d2841151845896ad725c0e1eac`

## Verificación Post-Deployment

- [ ] Esperar a que el build termine (5-10 min)
- [ ] Verificar URL: `https://financetracker.onrender.com`
- [ ] Probar agregar transacción de BTC
- [ ] Verificar que los precios cargan correctamente
- [ ] Verificar gráfico de evolución
- [ ] Probar agregar transacción de acciones MX
- [ ] Verificar gráficos de composición

## Troubleshooting

Si algo falla:

- [ ] Revisar logs en Render dashboard
- [ ] Verificar que la variable de entorno esté configurada
- [ ] Verificar que el build command se ejecutó correctamente
- [ ] Re-deploy manual si es necesario

## Post-Launch Opcional

- [ ] Configurar dominio personalizado
- [ ] Configurar alertas de monitoreo
- [ ] Configurar auto-scaling (si es necesario)
- [ ] Documentar URL de producción

---

**URL esperada:** `https://financetracker.onrender.com`

**Tiempo estimado total:** 15-20 minutos
