# ⚡ Guide de Démarrage Rapide

Ce guide vous permet de lancer la plateforme en **moins de 10 minutes** !

## 🎯 Prérequis

- [ ] Docker installé ([Télécharger Docker](https://www.docker.com/get-started))
- [ ] Docker Compose installé (inclus avec Docker Desktop)
- [ ] Compte Assembly AI gratuit ([S'inscrire](https://www.assemblyai.com/))

## 📦 Étapes d'installation

### 1. Structure du projet

Créez la structure suivante :

```
ai-transcription-platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── transcription.py
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── transcription.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── transcriptions.py
│   │   │       ├── users.py
│   │   │       └── auth.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── transcription_service.py
│   │   │   ├── youtube_service.py
│   │   │   └── correction_service.py
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   └── transcription_tasks.py
│   │   └── core/
│   │       ├── __init__.py
│   │       └── celery_app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── [Fichiers Sneat Template]
│   ├── Dockerfile
│   └── .env.local
├── docker-compose.yml
└── README.md
```

### 2. Copier les fichiers fournis

Les fichiers ont été générés et sont disponibles dans ce livrable :

1. **Backend** : Copiez tous les fichiers `backend_*` dans `backend/app/`
2. **Frontend** : Copiez tous les fichiers `frontend_*` dans `frontend/src/components/`
3. **Docker** : Copiez `docker-compose.yml` à la racine
4. **Documentation** : `README.md`, `ARCHITECTURE_ET_IMPLEMENTATION.md`, `presentation.html`

### 3. Configuration Assembly AI

1. Allez sur https://www.assemblyai.com/
2. Créez un compte gratuit
3. Copiez votre clé API depuis le dashboard
4. Créez `backend/.env` :

```env
ASSEMBLYAI_API_KEY=votre_cle_api_ici
DATABASE_URL=postgresql://aiplatform:aiplatform_password@postgres:5432/aiplatform_db
REDIS_URL=redis://:redis_password@redis:6379/0
CELERY_BROKER_URL=redis://:redis_password@redis:6379/1
CELERY_RESULT_BACKEND=redis://:redis_password@redis:6379/2
SECRET_KEY=changez-cette-cle-en-production
ENVIRONMENT=development
DEBUG=true
```

### 4. Télécharger le template Sneat

1. Téléchargez Sneat depuis https://themeselection.com/item/sneat-mui-nextjs-admin-template/
2. Extrayez dans `frontend/`
3. Créez `frontend/.env.local` :

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=development
```

### 5. Créer les fichiers __init__.py

```bash
# Backend
touch backend/app/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/api/__init__.py
touch backend/app/api/v1/__init__.py
touch backend/app/services/__init__.py
touch backend/app/tasks/__init__.py
touch backend/app/core/__init__.py
```

### 6. Lancer la plateforme

```bash
# À la racine du projet
docker-compose up -d
```

### 7. Vérifier le déploiement

Attendez 30 secondes que tous les services démarrent, puis vérifiez :

```bash
# Status des containers
docker-compose ps

# Logs backend
docker-compose logs -f backend

# Logs frontend
docker-compose logs -f frontend
```

### 8. Accéder à l'application

- 🌐 **Frontend** : http://localhost:3000
- 🔌 **API** : http://localhost:8000
- 📚 **Docs API** : http://localhost:8000/docs
- 🌸 **Flower (Celery)** : http://localhost:5555

## ✅ Test rapide

1. Ouvrez http://localhost:3000
2. Collez une URL YouTube (ex: https://www.youtube.com/watch?v=dQw4w9WgXcQ)
3. Cliquez sur "Lancer la transcription"
4. Observez la progression !

## 🐛 Dépannage

### Le backend ne démarre pas

```bash
# Vérifier les logs
docker-compose logs backend

# Problème commun : clé Assembly AI manquante
# Solution : Vérifiez backend/.env
```

### Le frontend ne démarre pas

```bash
# Vérifier les logs
docker-compose logs frontend

# Problème commun : node_modules manquants
# Solution : Reconstruire l'image
docker-compose build frontend
docker-compose up -d frontend
```

### Celery worker ne traite pas les jobs

```bash
# Vérifier le worker
docker-compose logs celery_worker

# Redémarrer le worker
docker-compose restart celery_worker
```

### La base de données n'est pas accessible

```bash
# Vérifier PostgreSQL
docker-compose logs postgres

# Se connecter à PostgreSQL
docker-compose exec postgres psql -U aiplatform -d aiplatform_db
```

## 🔧 Commandes utiles

```bash
# Arrêter tous les services
docker-compose down

# Arrêter et supprimer les volumes (⚠️ supprime les données)
docker-compose down -v

# Voir les logs en temps réel
docker-compose logs -f

# Reconstruire les images
docker-compose build

# Redémarrer un service spécifique
docker-compose restart backend

# Exécuter une commande dans un container
docker-compose exec backend python -m app.main

# Voir l'utilisation des ressources
docker stats
```

## 📊 Monitoring

### Flower (Celery)

Lancez Flower pour monitorer les tâches Celery :

```bash
docker-compose --profile monitoring up -d
```

Accédez à http://localhost:5555

### PgAdmin (PostgreSQL)

Lancez PgAdmin pour gérer la base de données :

```bash
docker-compose --profile monitoring up -d pgadmin
```

Accédez à http://localhost:5050
- Email : admin@aiplatform.com
- Mot de passe : admin_password

## 🚀 Passage en production

### 1. Variables d'environnement

Modifiez `backend/.env` :

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<générez-une-vraie-clé-sécurisée>
```

### 2. Nginx

```bash
# Lancez Nginx
docker-compose --profile production up -d nginx
```

### 3. HTTPS/SSL

Ajoutez vos certificats SSL dans `nginx/ssl/`

### 4. Sauvegarde base de données

```bash
# Backup manuel
docker-compose exec postgres pg_dump -U aiplatform aiplatform_db > backup.sql

# Restauration
docker-compose exec -T postgres psql -U aiplatform aiplatform_db < backup.sql
```

## 📈 Métriques de performance

**Temps moyens attendus :**
- Téléchargement audio (vidéo 10min) : ~30 secondes
- Transcription Assembly AI : ~1-2 minutes
- Post-traitement : ~5 secondes
- **Total : 2-3 minutes pour 10 minutes de vidéo**

## 🎓 Prochaines étapes

1. ✅ Familiarisez-vous avec l'interface
2. 📚 Consultez [ARCHITECTURE_ET_IMPLEMENTATION.md](./ARCHITECTURE_ET_IMPLEMENTATION.md)
3. 🎨 Ouvrez [presentation.html](./presentation.html) dans votre navigateur
4. 🔧 Personnalisez le frontend Sneat selon vos besoins
5. 🚀 Déployez en production !

## 💡 Conseils

- **Free Tier Assembly AI** : 5h/mois gratuit (parfait pour tester)
- **Optimisation** : Activez le cache Redis pour les vidéos déjà traitées
- **Scalabilité** : Ajoutez plus de workers Celery si nécessaire
- **Logs** : Configurez un système de logging centralisé pour la production

## 🤝 Besoin d'aide ?

- 📖 Documentation complète : [README.md](./README.md)
- 🏗️ Architecture : [ARCHITECTURE_ET_IMPLEMENTATION.md](./ARCHITECTURE_ET_IMPLEMENTATION.md)
- 🐛 Issues : Créez une issue sur GitHub

---

**Temps estimé de setup : 10 minutes**  
**Difficulté : ⭐⭐☆☆☆ (Facile avec Docker)**

Bonne chance ! 🚀
