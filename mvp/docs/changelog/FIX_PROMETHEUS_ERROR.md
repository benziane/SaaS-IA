# 🔧 Fix: ModuleNotFoundError: No module named 'prometheus_client'

## 🚨 Problème

```
ModuleNotFoundError: No module named 'prometheus_client'
```

Le module `prometheus_client` n'était pas installé dans l'image Docker backend.

---

## ✅ Solution (DÉJÀ APPLIQUÉE)

### 1. Dépendances ajoutées à `requirements.txt`

```txt
# Monitoring & Observability
prometheus-client==0.19.0
pyyaml==6.0.1  # For AI Router config
```

### 2. Rebuild de l'image Docker nécessaire

---

## 🚀 Comment corriger (2 options)

### **Option A — Script automatique (RECOMMANDÉ)**

```powershell
cd C:\Users\ibzpc\Git\SaaS-IA\mvp\tools\env_mng
.\rebuild-backend.ps1
```

Ce script va :
- ✅ Arrêter les conteneurs
- ✅ Rebuild l'image backend (avec les nouvelles dépendances)
- ✅ Redémarrer les services
- ✅ Vérifier que le backend est prêt

**Durée : 2-3 minutes**

---

### **Option B — Commandes manuelles**

```powershell
cd C:\Users\ibzpc\Git\SaaS-IA\mvp

# 1. Arrêter les conteneurs
docker-compose down

# 2. Rebuild backend (sans cache)
docker-compose build backend --no-cache

# 3. Redémarrer
docker-compose up -d

# 4. Vérifier les logs
docker-compose logs -f backend
```

---

## 🧪 Vérification

### 1. Backend doit démarrer sans erreur

```bash
docker-compose logs backend | grep "prometheus_client"
# Aucun résultat = OK
```

### 2. Health check

```bash
curl http://localhost:8004/health
# Doit retourner: {"status":"healthy"}
```

### 3. Test AI Router

```bash
cd C:\Users\ibzpc\Git\SaaS-IA\mvp\backend
python test_ai_router.py
```

### 4. Test dans la page debug

1. Ouvrir : http://localhost:5174/transcription/debug
2. Coller une URL YouTube
3. Cliquer "Transcribe"
4. Observer les logs backend :

```bash
docker-compose logs -f backend | grep "ai_router"
```

Vous devriez voir :
```
ai_router_start
content_classified
model_selected
prompt_selected
ai_router_success
```

---

## 📊 Pourquoi cette erreur ?

L'AI Router Phase 1 utilise **Prometheus metrics** pour l'observabilité :

```python
# backend/app/ai_assistant/classification/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info
```

Ces métriques permettent de monitorer :
- Nombre de classifications par domaine
- Temps de traitement
- Modèles sélectionnés
- Confiance des classifications

**C'est une feature "Enterprise S++"** qui nécessite `prometheus_client`.

---

## 🎯 Résultat attendu

Après rebuild :

✅ Backend démarre sans erreur  
✅ AI Router fonctionne  
✅ Métriques Prometheus enregistrées  
✅ Page debug transcription opérationnelle  
✅ Logs `ai_router_*` visibles  

---

## 🆘 Si le problème persiste

### 1. Vérifier que les dépendances sont bien installées

```bash
docker-compose exec backend pip list | grep prometheus
# Doit afficher: prometheus-client 0.19.0
```

### 2. Vérifier le Dockerfile

Le `Dockerfile` backend doit contenir :

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### 3. Rebuild complet (force)

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

---

## 📝 Fichiers modifiés

- ✅ `backend/requirements.txt` (ajout prometheus-client + pyyaml)
- ✅ `tools/env_mng/rebuild-backend.ps1` (nouveau script)
- ✅ `FIX_PROMETHEUS_ERROR.md` (ce document)

---

## 🚀 Prochaines étapes

Une fois le backend redémarré :

1. **Tester l'AI Router** :
   ```bash
   cd backend
   python test_ai_router.py
   ```

2. **Tester la transcription avec AI Router** :
   - Ouvrir http://localhost:5174/transcription/debug
   - Transcrire une vidéo YouTube
   - Observer les logs `ai_router_*`

3. **Vérifier les métriques Prometheus** :
   ```bash
   curl http://localhost:8004/metrics | grep ai_router
   ```

---

**Grade : S++ — Fix appliqué, prêt pour rebuild**

