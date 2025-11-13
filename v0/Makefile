.PHONY: help build up down restart logs clean install test

help: ## Afficher l'aide
	@echo "Commandes disponibles :"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Construire les images Docker
	docker-compose build

up: ## Démarrer tous les services
	docker-compose up -d
	@echo "✅ Services démarrés !"
	@echo "🌐 Frontend: http://localhost:3000"
	@echo "🔌 Backend API: http://localhost:8000"
	@echo "📚 API Docs: http://localhost:8000/docs"

down: ## Arrêter tous les services
	docker-compose down

restart: ## Redémarrer tous les services
	docker-compose restart

logs: ## Afficher les logs
	docker-compose logs -f

logs-backend: ## Afficher les logs du backend
	docker-compose logs -f backend

logs-frontend: ## Afficher les logs du frontend
	docker-compose logs -f frontend

clean: ## Nettoyer les volumes et images
	docker-compose down -v
	docker system prune -f

install-backend: ## Installer les dépendances backend (mode local)
	cd backend && pip install -r requirements.txt
	python -m spacy download fr_core_news_md
	python -m spacy download en_core_web_md

install-frontend: ## Installer les dépendances frontend (mode local)
	cd frontend && npm install

dev-backend: ## Lancer le backend en mode développement (local)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Lancer le frontend en mode développement (local)
	cd frontend && npm run dev

test-backend: ## Lancer les tests backend
	cd backend && pytest

test-frontend: ## Lancer les tests frontend
	cd frontend && npm run test

shell-backend: ## Ouvrir un shell dans le conteneur backend
	docker-compose exec backend bash

shell-db: ## Ouvrir un shell PostgreSQL
	docker-compose exec db psql -U postgres -d transcription_db

db-migrate: ## Créer une nouvelle migration
	docker-compose exec backend alembic revision --autogenerate -m "$(message)"

db-upgrade: ## Appliquer les migrations
	docker-compose exec backend alembic upgrade head

status: ## Afficher le statut des services
	docker-compose ps

health: ## Vérifier la santé de l'API
	curl http://localhost:8000/api/v1/health

# Production
prod-build: ## Construire pour la production
	docker-compose -f docker-compose.prod.yml build

prod-up: ## Démarrer en mode production
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Arrêter en mode production
	docker-compose -f docker-compose.prod.yml down

# Dev tools
format-backend: ## Formater le code backend
	cd backend && black app/ && isort app/

lint-backend: ## Linter le code backend
	cd backend && flake8 app/ && mypy app/

format-frontend: ## Formater le code frontend
	cd frontend && npm run format
