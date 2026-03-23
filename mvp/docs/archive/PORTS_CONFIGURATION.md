# 📊 CONFIGURATION DES PORTS - SAAS-IA

**Date** : 2025-11-14  
**Version** : 1.0.0  
**Statut** : ✅ VALIDÉ

---

## 🎯 PORTS SAAS-IA

| Service | Port | URL | Statut |
|---------|------|-----|--------|
| **Frontend (Next.js)** | **3002** | `http://localhost:3002` | ✅ |
| **Backend (FastAPI)** | **8004** | `http://localhost:8004` | ✅ |
| **PostgreSQL** | **5435** | `localhost:5435` | ✅ |
| **Redis** | **6382** | `localhost:6382` | ✅ |

---

## 🚨 CONFLIT DE PORTS RÉSOLU

### Problème Initial

Le port **5174** était initialement choisi pour le frontend SaaS-IA lors de l'intégration Sneat, mais ce port est **déjà utilisé par WeLAB**.

### Solution

Retour au port **3002** qui était l'ancien port de SaaS-IA et qui est **libre**.

### Historique

| Date | Action | Port | Raison |
|------|--------|------|--------|
| 2025-11-14 | Initial | 3002 | Port par défaut MVP |
| 2025-11-14 | Changement | 5174 | Intégration Sneat (erreur) |
| 2025-11-14 | Correction | 3002 | Conflit avec WeLAB |

---

## 📋 PORTS UTILISÉS PAR LES AUTRES PROJETS

### WeLAB

| Service | Port | URL |
|---------|------|-----|
| Frontend (Next.js) | **5174** | `http://localhost:5174` |
| Backend (FastAPI) | **8001** | `http://localhost:8001` |
| PostgreSQL | 5432 | `localhost:5432` |
| Redis | 6379 | `localhost:6379` |

### LabSaaS

| Service | Port | URL |
|---------|------|-----|
| Frontend (Next.js) | **5173** | `http://localhost:5173` |
| Backend (FastAPI) | **8000** | `http://localhost:8000` |
| PostgreSQL | 5432 | `localhost:5432` |
| Redis | 6379 | `localhost:6379` |

---

## ✅ RÈGLES DE GESTION DES PORTS

### 1. Éviter les Conflits

- ✅ **Toujours vérifier** les ports utilisés par les autres projets avant d'en choisir un nouveau
- ✅ **Documenter** les ports dans un fichier `PORTS_CONFIGURATION.md`
- ✅ **Utiliser des ports distincts** pour chaque projet

### 2. Ports Standards

| Service | Plage Recommandée | Exemple |
|---------|-------------------|---------|
| Frontend | 3000-3999, 5000-5999 | 3002 |
| Backend | 8000-8999 | 8004 |
| PostgreSQL | 5400-5499 | 5435 |
| Redis | 6300-6399 | 6382 |

### 3. Configuration

**Frontend (Next.js)** :
```json
// package.json
{
  "scripts": {
    "dev": "next dev -p 3002",
    "start": "next start -p 3002"
  }
}
```

**Backend (FastAPI)** :
```bash
uvicorn app.main:app --reload --port 8004
```

**Docker Compose** :
```yaml
services:
  postgres:
    ports:
      - "5435:5432"
  redis:
    ports:
      - "6382:6379"
```

---

## 🔧 SCRIPTS MIS À JOUR

Les scripts suivants ont été mis à jour pour utiliser le port **3002** :

- ✅ `mvp/tools/env_mng/check-status.ps1`
- ✅ `mvp/tools/env_mng/restart-env.ps1`
- ✅ `mvp/tools/env_mng/start-env.ps1`
- ✅ `mvp/tools/env_mng/stop-env.ps1`
- ✅ `mvp/tools/env_mng/quick-commands.bat`
- ✅ `mvp/tools/env_mng/README.md`
- ✅ `mvp/tools/env_mng/INDEX.md`
- ✅ `mvp/tools/env_mng/TESTS_VALIDATION.md`
- ✅ `mvp/frontend/SNEAT_INTEGRATION_FINAL_REPORT.md`
- ✅ `mvp/frontend/TESTS_VALIDATION_SNEAT.md`

---

## 📝 VARIABLES D'ENVIRONNEMENT

### Frontend `.env.local`

```bash
# API Backend
NEXT_PUBLIC_API_URL=http://localhost:8004

# Environment
NODE_ENV=development
```

### Backend `.env`

```bash
# Database
DATABASE_URL=postgresql://saas_ia_user:saas_ia_dev_password@localhost:5435/saas_ia

# Redis
REDIS_URL=redis://localhost:6382

# CORS (Frontend URL)
CORS_ORIGINS=http://localhost:3002,http://localhost:8004

# JWT
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
```

---

## 🚀 COMMANDES RAPIDES

### Démarrer l'environnement

```powershell
cd C:\Users\ibzpc\Git\SaaS-IA\mvp\tools\env_mng
.\start-env.bat
```

### Vérifier les ports

```powershell
.\check-status.bat
```

### Ouvrir les services

```powershell
# Frontend
start http://localhost:3002

# Backend API
start http://localhost:8004

# API Docs (Swagger)
start http://localhost:8004/docs
```

---

## 🧪 TESTS

### Vérifier que les ports sont libres

```powershell
# PowerShell
Test-NetConnection -ComputerName localhost -Port 3002
Test-NetConnection -ComputerName localhost -Port 8004
Test-NetConnection -ComputerName localhost -Port 5435
Test-NetConnection -ComputerName localhost -Port 6382
```

### Vérifier les services

```powershell
# Frontend
curl http://localhost:3002

# Backend Health
curl http://localhost:8004/health

# Backend API Docs
curl http://localhost:8004/docs
```

---

## 📚 DOCUMENTATION ASSOCIÉE

- `mvp/tools/env_mng/README.md` - Guide complet des scripts d'environnement
- `mvp/frontend/SNEAT_INTEGRATION_FINAL_REPORT.md` - Rapport intégration Sneat
- `mvp/frontend/TESTS_VALIDATION_SNEAT.md` - Tests validation frontend
- `mvp/backend/README.md` - Documentation backend

---

## ✅ CHECKLIST AVANT DÉMARRAGE

- [ ] Vérifier que les ports 3002, 8004, 5435, 6382 sont libres
- [ ] Vérifier que Docker Desktop est démarré
- [ ] Vérifier que les fichiers `.env` sont configurés
- [ ] Lancer `start-env.bat`
- [ ] Vérifier avec `check-status.bat`
- [ ] Ouvrir `http://localhost:3002`

---

**Créé par** : Assistant IA  
**Date** : 2025-11-14  
**Version** : 1.0.0  
**Statut** : ✅ VALIDÉ

