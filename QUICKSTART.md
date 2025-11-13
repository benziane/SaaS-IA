# 🚀 Guide de Démarrage Rapide

## Installation en 3 étapes

### 1. Prérequis
- Docker et Docker Compose installés
- Git

### 2. Cloner et configurer

```bash
# Cloner le repository
git clone <repository-url>
cd SaaS-IA

# Créer les fichiers .env (déjà configurés pour le développement)
# Rien à faire, les fichiers .env sont déjà présents !
```

### 3. Lancer l'application

```bash
# Avec Makefile (recommandé)
make up

# Ou avec Docker Compose directement
docker-compose up -d
```

## Accès aux services

Une fois les services démarrés (environ 2-3 minutes pour le premier lancement) :

- 🌐 **Interface Web** : http://localhost:3000
- 🔌 **API Backend** : http://localhost:8000
- 📚 **Documentation API** : http://localhost:8000/docs
- 🗄️ **pgAdmin** (optionnel) : http://localhost:5050
  - Email : admin@admin.com
  - Password : admin

## Premier test

1. Ouvrez http://localhost:3000
2. Collez une URL YouTube dans le formulaire
3. Cliquez sur "Lancer la transcription"
4. Regardez la progression en temps réel !

## Commandes utiles

```bash
# Voir les logs
make logs

# Logs backend uniquement
make logs-backend

# Logs frontend uniquement
make logs-frontend

# Statut des services
make status

# Vérifier la santé de l'API
make health

# Redémarrer tous les services
make restart

# Arrêter tous les services
make down

# Nettoyer complètement (⚠️ supprime les données)
make clean
```

## Résolution de problèmes

### Le backend ne démarre pas

```bash
# Vérifier les logs
make logs-backend

# Redémarrer le service
docker-compose restart backend
```

### Le frontend ne se connecte pas au backend

```bash
# Vérifier que le backend est accessible
curl http://localhost:8000/api/v1/health

# Redémarrer le frontend
docker-compose restart frontend
```

### Problèmes de base de données

```bash
# Vérifier PostgreSQL
docker-compose logs db

# Se connecter à la base de données
make shell-db

# Recréer la base de données (⚠️ perte de données)
docker-compose down -v
docker-compose up -d
```

### Le téléchargement YouTube échoue

Assurez-vous que :
- L'URL YouTube est valide et publique
- La vidéo n'est pas géo-restreinte
- Vous avez une connexion internet

## Mode développement local (sans Docker)

### Backend

```bash
cd backend

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Installer les dépendances
make install-backend

# Lancer le serveur
make dev-backend
```

### Frontend

```bash
cd frontend

# Installer les dépendances
make install-frontend

# Lancer le serveur
make dev-frontend
```

## Prochaines étapes

1. ✅ Testez avec différentes vidéos YouTube
2. ✅ Explorez la documentation API : http://localhost:8000/docs
3. ✅ Consultez le README.md pour plus de détails
4. ✅ Lisez docs/ARCHITECTURE.md pour comprendre l'architecture
5. ✅ Regardez docs/API.md pour les détails de l'API

## Support

- 📖 Documentation complète : [README.md](README.md)
- 🏗️ Architecture : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 🔌 API : [docs/API.md](docs/API.md)
- 🐛 Issues : GitHub Issues

Bon codage ! 🎉
