# 🧪 Guide de Tests - SaaS-IA MVP

## 📋 Vue d'ensemble

Ce guide contient toutes les commandes pour tester le MVP SaaS-IA.

**Note** : Les tests sont documentés ici car ils nécessitent que les services Docker soient démarrés.
Vous devez exécuter ces tests manuellement.

---

## 🚀 Étape 1 : Démarrer les services

```bash
cd C:\Users\ibzpc\Git\SaaS-IA\mvp\backend
docker-compose up -d
```

Attendez 30-60 secondes que tous les services démarrent.

### Vérifier le health check

```bash
curl http://localhost:8004/health
```

**Résultat attendu** :
```json
{
  "status": "healthy",
  "app_name": "SaaS-IA MVP",
  "environment": "development",
  "version": "1.0.0"
}
```

---

## 🔐 Étape 2 : Tester l'authentification

### 2.1 Créer un compte utilisateur

```bash
curl -X POST http://localhost:8004/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"test@example.com\", \"password\": \"password123\", \"full_name\": \"Test User\"}"
```

**Résultat attendu** :
```json
{
  "id": "...",
  "email": "test@example.com",
  "full_name": "Test User",
  "role": "user",
  "is_active": true,
  "created_at": "..."
}
```

### 2.2 Se connecter

```bash
curl -X POST http://localhost:8004/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123"
```

**Résultat attendu** :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**⚠️ IMPORTANT** : Copiez le `access_token` pour les tests suivants !

### 2.3 Obtenir les infos utilisateur

```bash
# Remplacez <TOKEN> par votre access_token
curl http://localhost:8004/api/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```

**Résultat attendu** :
```json
{
  "id": "...",
  "email": "test@example.com",
  "full_name": "Test User",
  "role": "user",
  "is_active": true,
  "created_at": "..."
}
```

---

## 🎙️ Étape 3 : Tester le module Transcription

### 3.1 Créer une transcription (Mode MOCK)

```bash
# Remplacez <TOKEN> par votre access_token
curl -X POST http://localhost:8004/api/transcription \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"video_url\": \"https://www.youtube.com/watch?v=dQw4w9WgXcQ\", \"language\": \"auto\"}"
```

**Résultat attendu** :
```json
{
  "id": "...",
  "user_id": "...",
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "language": "auto",
  "status": "pending",
  "text": null,
  "confidence": null,
  "duration_seconds": null,
  "error": null,
  "retry_count": 0,
  "created_at": "...",
  "updated_at": "...",
  "completed_at": null
}
```

**⚠️ IMPORTANT** : Copiez le `id` du job pour les tests suivants !

### 3.2 Vérifier le statut (après 2-3 secondes)

```bash
# Remplacez <TOKEN> et <JOB_ID>
curl http://localhost:8004/api/transcription/<JOB_ID> \
  -H "Authorization: Bearer <TOKEN>"
```

**Résultat attendu** (après traitement) :
```json
{
  "id": "...",
  "user_id": "...",
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "language": "auto",
  "status": "completed",
  "text": "Ceci est une transcription SIMULÉE pour le test...",
  "confidence": 0.95,
  "duration_seconds": 180,
  "error": null,
  "retry_count": 0,
  "created_at": "...",
  "updated_at": "...",
  "completed_at": "..."
}
```

### 3.3 Lister toutes les transcriptions

```bash
# Remplacez <TOKEN>
curl http://localhost:8004/api/transcription \
  -H "Authorization: Bearer <TOKEN>"
```

**Résultat attendu** :
```json
[
  {
    "id": "...",
    "status": "completed",
    ...
  }
]
```

### 3.4 Supprimer une transcription

```bash
# Remplacez <TOKEN> et <JOB_ID>
curl -X DELETE http://localhost:8004/api/transcription/<JOB_ID> \
  -H "Authorization: Bearer <TOKEN>"
```

**Résultat attendu** : HTTP 204 No Content

---

## 📊 Étape 4 : Tester le project-map.json

### 4.1 Générer le project-map

```bash
cd C:\Users\ibzpc\Git\SaaS-IA\mvp
.\update-project-map.bat
```

Ou avec Python directement :

```bash
cd C:\Users\ibzpc\Git\SaaS-IA\mvp\backend
python scripts\generate_project_map.py
```

### 4.2 Vérifier le fichier généré

```bash
cd C:\Users\ibzpc\Git\SaaS-IA\mvp
cat project-map.json
```

**Contenu attendu** :
- Section `project` avec nom, version, date
- Section `stats` avec totaux (modules, fichiers, lignes, etc.)
- Section `modules` avec détails de chaque module
- Section `api_endpoints` avec toutes les routes détectées
- Section `dependency_graph` avec les dépendances

---

## 🌐 Étape 5 : Tester via Swagger UI

### Accéder à Swagger

Ouvrez votre navigateur : **http://localhost:8004/docs**

### Tests dans Swagger

1. **Expand "Authentication"**
   - POST `/api/auth/register` → Créer un compte
   - POST `/api/auth/login` → Se connecter
   - GET `/api/auth/me` → Obtenir infos utilisateur

2. **Authorize** (bouton en haut à droite)
   - Cliquez sur "Authorize"
   - Collez votre `access_token`
   - Cliquez "Authorize" puis "Close"

3. **Expand "Transcription"**
   - POST `/api/transcription` → Créer une transcription
   - GET `/api/transcription/{job_id}` → Vérifier le statut
   - GET `/api/transcription` → Lister toutes les transcriptions
   - DELETE `/api/transcription/{job_id}` → Supprimer

---

## 🔍 Étape 6 : Vérifier les logs

### Logs backend

```bash
docker-compose logs -f backend
```

Vous devriez voir :
- `application_startup` au démarrage
- `database_initialized` après init DB
- `transcription_job_created` lors de la création
- `transcription_processing_started` au début du traitement
- `transcription_completed` à la fin

### Logs PostgreSQL

```bash
docker-compose logs -f db
```

### Logs Redis

```bash
docker-compose logs -f redis
```

---

## ✅ Checklist de Tests

### Infrastructure
- [ ] Docker Compose démarre sans erreur
- [ ] Health check retourne `{"status": "healthy"}`
- [ ] Swagger UI accessible sur http://localhost:8004/docs
- [ ] PostgreSQL accessible sur port 5435
- [ ] Redis accessible sur port 6382

### Authentification
- [ ] Création de compte réussie
- [ ] Login retourne un token JWT
- [ ] Token valide pour accéder aux endpoints protégés
- [ ] GET /api/auth/me retourne les infos utilisateur
- [ ] Tentative d'accès sans token retourne 401

### Module Transcription
- [ ] Création de job retourne status "pending"
- [ ] Job passe à "processing" puis "completed" (mode MOCK)
- [ ] Transcription MOCK contient le texte simulé
- [ ] Liste des transcriptions retourne les jobs de l'utilisateur
- [ ] Suppression de job réussie

### Project Map
- [ ] Script generate_project_map.py s'exécute sans erreur
- [ ] Fichier project-map.json généré à la racine
- [ ] JSON valide et bien formaté
- [ ] Contient toutes les sections attendues
- [ ] Routes API détectées correctement
- [ ] Métriques (lignes, complexité) présentes

---

## 🐛 Dépannage

### Erreur "Connection refused"

```bash
# Vérifier que les services sont démarrés
docker-compose ps

# Redémarrer si nécessaire
docker-compose restart
```

### Erreur "Database connection failed"

```bash
# Vérifier les logs PostgreSQL
docker-compose logs db

# Recréer la base de données
docker-compose down -v
docker-compose up -d
```

### Erreur "401 Unauthorized"

- Vérifiez que vous avez bien copié le token complet
- Le token expire après 30 minutes, reconnectez-vous
- Vérifiez que le header `Authorization: Bearer <token>` est correct

### Mode MOCK ne fonctionne pas

```bash
# Vérifier la variable d'environnement
docker-compose exec backend env | grep ASSEMBLYAI

# Devrait afficher : ASSEMBLYAI_API_KEY=MOCK
```

---

## 📝 Notes

- **Mode MOCK** : Par défaut, `ASSEMBLYAI_API_KEY=MOCK` dans `.env`
- **Ports** : Backend 8004, PostgreSQL 5435, Redis 6382
- **Logs structurés** : Utilisez `docker-compose logs -f backend` pour voir les événements
- **Swagger UI** : Interface interactive pour tester l'API

---

## 🎯 Résultat Attendu

Si tous les tests passent :
- ✅ Infrastructure opérationnelle
- ✅ Auth JWT fonctionnelle
- ✅ Module Transcription opérationnel (mode MOCK)
- ✅ Project-map.json généré avec succès
- ✅ API documentée et testable via Swagger

**MVP Backend : VALIDÉ ! 🎉**

---

**Date de création** : 2025-11-13  
**Version** : 1.0.0  
**Auteur** : SaaS-IA Team

