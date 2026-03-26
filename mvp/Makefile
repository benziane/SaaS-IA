# SaaS-IA Platform – Makefile
# Run `make help` to see all available targets.

COMPOSE        = docker compose
COMPOSE_MON    = $(COMPOSE) -f docker-compose.yml -f docker-compose.monitoring.yml
BACKEND_DIR    = ./backend
FRONTEND_DIR   = ./frontend
LOAD_DIR       = ./tests/load
COMPOSE_LOAD   = $(COMPOSE) -f $(LOAD_DIR)/docker-compose.load.yml

.DEFAULT_GOAL := help

# ── Development ──────────────────────────────────────────────

.PHONY: dev
dev: ## Start development environment (backend + infra)
	$(COMPOSE) up -d
	@echo "\n  Backend:  http://localhost:8004"
	@echo "  Flower:   http://localhost:5555"
	@echo "  Postgres: localhost:5435"
	@echo "  Redis:    localhost:6382\n"

.PHONY: dev-full
dev-full: ## Start everything including monitoring stack
	$(COMPOSE_MON) up -d
	@echo "\n  Backend:    http://localhost:8004"
	@echo "  Flower:     http://localhost:5555"
	@echo "  Jaeger UI:  http://localhost:16686"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  GlitchTip:  http://localhost:8090\n"

.PHONY: dev-frontend
dev-frontend: ## Start frontend dev server (Next.js)
	cd $(FRONTEND_DIR) && npm run dev

.PHONY: down
down: ## Stop all services
	$(COMPOSE) down

.PHONY: down-full
down-full: ## Stop all services including monitoring
	$(COMPOSE_MON) down

.PHONY: restart
restart: down dev ## Restart development environment

# ── Build ────────────────────────────────────────────────────

.PHONY: build
build: ## Build all Docker images
	$(COMPOSE) build

.PHONY: build-no-cache
build-no-cache: ## Build all Docker images without cache
	$(COMPOSE) build --no-cache

.PHONY: docker-build
docker-build: ## Build production backend Docker image
	docker build -t saas-ia-backend:latest $(BACKEND_DIR)

.PHONY: docker-push
docker-push: ## Push backend image to registry (set REGISTRY env var)
	@if [ -z "$(REGISTRY)" ]; then echo "Error: Set REGISTRY env var (e.g. REGISTRY=ghcr.io/org/repo)"; exit 1; fi
	docker tag saas-ia-backend:latest $(REGISTRY)/saas-ia-backend:latest
	docker push $(REGISTRY)/saas-ia-backend:latest

# ── Testing ──────────────────────────────────────────────────

.PHONY: test
test: ## Run all backend tests
	cd $(BACKEND_DIR) && python -m pytest -v

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	cd $(BACKEND_DIR) && python -m pytest --cov=app --cov-report=html --cov-report=term-missing

.PHONY: test-frontend
test-frontend: ## Run frontend tests
	cd $(FRONTEND_DIR) && npm run test

.PHONY: test-integration
test-integration: ## Run integration tests (mock mode, no external deps)
	cd $(BACKEND_DIR) && USE_REAL_DB=false USE_REAL_REDIS=false python -m pytest tests/integration/ -v --tb=short --no-cov

.PHONY: test-integration-real
test-integration-real: ## Run integration tests (real PostgreSQL + Redis)
	cd $(BACKEND_DIR) && USE_REAL_DB=true USE_REAL_REDIS=true python -m pytest tests/integration/ -v --tb=short --no-cov

# ── Load Testing ────────────────────────────────────────────

.PHONY: load-test
load-test: ## Run Locust load test (web UI at http://localhost:8089)
	cd $(LOAD_DIR) && locust -f locustfile.py
	@echo "\n  Locust UI: http://localhost:8089\n"

.PHONY: load-smoke
load-smoke: ## Quick smoke test (5 users, 30s)
	cd $(LOAD_DIR) && locust -f scenarios/smoke.py --headless -u 5 -r 5 -t 30s

.PHONY: load-stress
load-stress: ## Stress test (ramp to 500 users, 7m)
	cd $(LOAD_DIR) && locust -f scenarios/stress.py --headless -u 500 -r 50 -t 7m

.PHONY: load-soak
load-soak: ## Soak test (50 users, 30m)
	cd $(LOAD_DIR) && locust -f scenarios/soak.py --headless -u 50 -r 5 -t 30m

.PHONY: load-spike
load-spike: ## Spike test (0 -> 200 -> 0 users, 1m)
	cd $(LOAD_DIR) && locust -f scenarios/spike.py --headless -u 200 -r 200 -t 1m

.PHONY: load-k6
load-k6: ## Run k6 load test (staged ramp-up)
	cd $(LOAD_DIR) && k6 run k6_test.js

.PHONY: load-docker
load-docker: ## Start distributed Locust (4 workers, web UI at http://localhost:8089)
	$(COMPOSE_LOAD) up -d
	@echo "\n  Locust UI: http://localhost:8089\n"

.PHONY: load-docker-down
load-docker-down: ## Stop distributed Locust
	$(COMPOSE_LOAD) down

# ── Linting & Formatting ────────────────────────────────────

.PHONY: lint
lint: ## Run all linters (ruff + mypy + bandit)
	cd $(BACKEND_DIR) && python -m ruff check app/
	cd $(BACKEND_DIR) && python -m mypy app/ --ignore-missing-imports
	cd $(BACKEND_DIR) && python -m bandit -r app/ -q

.PHONY: format
format: ## Format code with ruff and black
	cd $(BACKEND_DIR) && python -m ruff check app/ --fix
	cd $(BACKEND_DIR) && python -m black app/

.PHONY: lint-frontend
lint-frontend: ## Lint frontend code
	cd $(FRONTEND_DIR) && npm run lint

# ── Database ─────────────────────────────────────────────────

.PHONY: migrate
migrate: ## Run database migrations (alembic upgrade head)
	cd $(BACKEND_DIR) && alembic upgrade head

.PHONY: migrate-docker
migrate-docker: ## Run migrations inside the backend container
	$(COMPOSE) exec saas-ia-backend alembic upgrade head

.PHONY: migration
migration: ## Generate a new migration (usage: make migration MSG="add users table")
	cd $(BACKEND_DIR) && alembic revision --autogenerate -m "$(MSG)"

.PHONY: migrate-history
migrate-history: ## Show migration history
	cd $(BACKEND_DIR) && alembic history --verbose

.PHONY: seed
seed: ## Seed database with test data
	cd $(BACKEND_DIR) && python scripts/seed_data.py

.PHONY: seed-docker
seed-docker: ## Seed database inside the backend container
	$(COMPOSE) exec saas-ia-backend python scripts/seed_data.py

# ── Logs & Monitoring ───────────────────────────────────────

.PHONY: logs
logs: ## Show logs for all services (follow mode)
	$(COMPOSE) logs -f

.PHONY: logs-backend
logs-backend: ## Show backend logs only
	$(COMPOSE) logs -f saas-ia-backend

.PHONY: logs-worker
logs-worker: ## Show worker logs only
	$(COMPOSE) logs -f worker

# ── Maintenance ─────────────────────────────────────────────

.PHONY: clean
clean: ## Stop containers, remove volumes, prune images
	$(COMPOSE) down -v --remove-orphans
	docker image prune -f

.PHONY: clean-all
clean-all: ## Full cleanup including named volumes (DESTROYS DATA)
	$(COMPOSE_MON) down -v --remove-orphans
	docker image prune -af

.PHONY: shell
shell: ## Open a shell in the backend container
	$(COMPOSE) exec saas-ia-backend bash

.PHONY: dbshell
dbshell: ## Open psql shell in the postgres container
	$(COMPOSE) exec postgres psql -U saas_ia_user -d saas_ia

.PHONY: health
health: ## Check health of all services
	@echo "Backend:"
	@curl -sf http://localhost:8004/health/ready | python -m json.tool 2>/dev/null || echo "  DOWN"
	@echo "\nPostgres:"
	@$(COMPOSE) exec postgres pg_isready -U saas_ia_user -d saas_ia 2>/dev/null || echo "  DOWN"
	@echo "Redis:"
	@$(COMPOSE) exec redis redis-cli ping 2>/dev/null || echo "  DOWN"

.PHONY: ps
ps: ## Show running containers and their status
	$(COMPOSE) ps

# ── Help ─────────────────────────────────────────────────────

.PHONY: help
help: ## Show this help message
	@echo "SaaS-IA Platform – Available targets:\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
