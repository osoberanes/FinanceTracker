# Instrucciones para Subir a GitHub

## Opción 1: Crear repositorio desde GitHub Web (Recomendado)

1. **Ve a GitHub**: https://github.com/new

2. **Configura el repositorio**:
   - Repository name: `FinanceTracker`
   - Description: `Investment portfolio tracker with real-time updates, analytics, and interactive charts`
   - Visibility: Public (o Private si prefieres)
   - **NO** inicialices con README, .gitignore o license (ya los tenemos)

3. **Haz clic en "Create repository"**

4. **En tu terminal, ejecuta estos comandos**:

```bash
cd /home/oscar/claude/FinanceTracker
git remote add origin https://github.com/osoberanes/FinanceTracker.git
git branch -M main
git push -u origin main
```

## Opción 2: Usando SSH (si tienes SSH keys configuradas)

```bash
cd /home/oscar/claude/FinanceTracker
git remote add origin git@github.com:osoberanes/FinanceTracker.git
git branch -M main
git push -u origin main
```

## Opción 3: Instalar GitHub CLI

```bash
# Instalar gh CLI
sudo apt install gh

# Autenticarse
gh auth login

# Crear y subir repo
gh repo create FinanceTracker --public --source=. --description="Investment portfolio tracker" --push
```

## Verificar que el repositorio local está listo

El repositorio local ya está configurado y tiene:
- ✅ Git inicializado
- ✅ Archivos commiteados
- ✅ .gitignore configurado
- ✅ 11 archivos listos para subir

Solo falta conectarlo con GitHub y hacer push.
