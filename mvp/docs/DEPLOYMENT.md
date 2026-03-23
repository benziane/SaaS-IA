# Guide de Deploiement - SaaS-IA

## Pre-requis

- Docker 24+ et Docker Compose v2
- Node.js 18+ (frontend)
- Un compte Stripe (optionnel, pour les paiements)
- Cles API pour au moins un provider IA (Gemini, Claude, ou Groq)

## 1. Deploiement local (developpement)

### Backend + Services

```bash
cd mvp

# Copier et configurer l'environnement
cp backend/.env.example backend/.env
```

Editer `backend/.env` :

```env
# Securite (OBLIGATOIRE - generer une cle forte)
SECRET_KEY=votre-cle-secrete-aleatoire-de-64-chars

# Base de donnees (defaut Docker)
DATABASE_URL=postgresql://saas_ia_user:saas_ia_dev_password@localhost:5435/saas_ia

# Redis
REDIS_URL=redis://localhost:6382

# AI Providers (au moins un requis)
GEMINI_API_KEY=votre_cle_gemini
CLAUDE_API_KEY=votre_cle_claude
GROQ_API_KEY=votre_cle_groq

# Transcription (MOCK pour tester sans API)
ASSEMBLYAI_API_KEY=MOCK

# Stripe (optionnel)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO_MONTHLY=price_...

# Application
ENVIRONMENT=development
DEBUG=True
CORS_ORIGINS=http://localhost:3002,http://localhost:8004
```

Lancer les services :

```bash
docker compose up -d
```

Services demarre :
- Backend API : http://localhost:8004
- PostgreSQL : localhost:5435
- Redis : localhost:6382
- Celery Worker : en arriere-plan
- Flower : http://localhost:5555

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend : http://localhost:3002

### Migrations Alembic

```bash
cd backend

# Appliquer toutes les migrations
alembic upgrade head

# Verifier le statut
alembic current

# Voir l'historique
alembic history
```

## 2. Deploiement production

### Variables d'environnement production

```env
# SECURITE CRITIQUE
SECRET_KEY=<generer: python -c "import secrets; print(secrets.token_urlsafe(64))">
ENVIRONMENT=production
DEBUG=False

# Base de donnees (managed PostgreSQL recommande)
DATABASE_URL=postgresql://user:password@db-host:5432/saas_ia

# Redis (managed Redis recommande)
REDIS_URL=redis://redis-host:6379

# AI Providers
GEMINI_API_KEY=<production_key>
ASSEMBLYAI_API_KEY=<production_key>

# CORS (domaine production uniquement)
CORS_ORIGINS=https://app.votre-domaine.com

# Stripe (mode live)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO_MONTHLY=price_...
```

### Docker Compose production

Creer `docker-compose.prod.yml` :

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
      - DEBUG=False
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    command: celery -A app.celery_app worker --loglevel=warning --concurrency=4

  flower:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    environment:
      - REDIS_URL=${REDIS_URL}
    ports:
      - "5555:5555"
    command: celery -A app.celery_app flower --port=5555 --basic_auth=admin:password
```

### Nginx reverse proxy

```nginx
server {
    listen 443 ssl http2;
    server_name api.votre-domaine.com;

    ssl_certificate /etc/letsencrypt/live/api.votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.votre-domaine.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE support
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    location /v1/ {
        proxy_pass http://localhost:8000/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 443 ssl http2;
    server_name app.votre-domaine.com;

    ssl_certificate /etc/letsencrypt/live/app.votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.votre-domaine.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }
}
```

### Frontend production build

```bash
cd frontend

# Variables d'environnement frontend
echo "NEXT_PUBLIC_API_URL=https://api.votre-domaine.com" > .env.production

# Build
npm run build

# Lancer en production
npm start
# ou avec PM2 :
pm2 start npm --name "saas-ia-frontend" -- start
```

## 3. Configuration Stripe

### Mode test

1. Creer un compte sur https://dashboard.stripe.com
2. Aller dans Developers > API Keys
3. Copier la Secret Key (`sk_test_...`) dans `.env`

### Creer un produit et un prix

```bash
# Via Stripe CLI ou dashboard
# Dashboard > Products > Add product
# Nom: "SaaS-IA Pro"
# Prix: 19 EUR/mois (recurring)
# Copier le Price ID (price_...) dans STRIPE_PRICE_PRO_MONTHLY
```

### Configurer le webhook

1. Dashboard > Developers > Webhooks > Add endpoint
2. URL : `https://api.votre-domaine.com/api/billing/webhook`
3. Events :
   - `checkout.session.completed`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
4. Copier le Signing Secret (`whsec_...`) dans `STRIPE_WEBHOOK_SECRET`

### Test local avec Stripe CLI

```bash
# Installer Stripe CLI
# https://stripe.com/docs/stripe-cli

# Ecouter les webhooks en local
stripe listen --forward-to localhost:8004/api/billing/webhook

# Dans un autre terminal, tester
stripe trigger checkout.session.completed
```

## 4. Monitoring production

### Health checks

```bash
# API health
curl https://api.votre-domaine.com/health

# Modules charges
curl https://api.votre-domaine.com/api/modules
```

### Prometheus

Endpoint : `GET /metrics` (protege par token en production)

```bash
curl -H "X-Metrics-Token: $SECRET_KEY" https://api.votre-domaine.com/metrics
```

### Flower (Celery monitoring)

Accessible sur le port 5555. En production, proteger avec basic auth :

```bash
celery -A app.celery_app flower --port=5555 --basic_auth=admin:mot_de_passe_fort
```

### Logs

Les logs sont structures en JSON via `structlog`. Configurer la collecte avec :
- Datadog, Grafana Loki, ou ELK Stack
- `LOG_LEVEL=INFO` en production (WARNING pour moins de bruit)

## 5. Backup et maintenance

### Backup PostgreSQL

```bash
# Backup
pg_dump -U saas_ia_user -h localhost -p 5435 saas_ia > backup_$(date +%Y%m%d).sql

# Restore
psql -U saas_ia_user -h localhost -p 5435 saas_ia < backup_20260323.sql
```

### Migrations

```bash
cd backend

# Voir les migrations en attente
alembic current
alembic history

# Appliquer les nouvelles migrations
alembic upgrade head

# Rollback une migration
alembic downgrade -1
```

### Reset quotas mensuels

Les quotas sont automatiquement geres par `BillingService.get_user_quota()` qui cree une nouvelle periode quand l'ancienne expire. Pour un reset manuel :

```python
# Via shell Python
from app.modules.billing.service import BillingService
await BillingService.reset_monthly_quotas(session)
```

## 6. Checklist pre-production

- [ ] `SECRET_KEY` genere avec 64+ caracteres aleatoires
- [ ] `ENVIRONMENT=production` et `DEBUG=False`
- [ ] `CORS_ORIGINS` restreint au domaine production
- [ ] PostgreSQL et Redis en mode managed (backup automatique)
- [ ] HTTPS configure (Let's Encrypt ou certificat)
- [ ] Stripe en mode live avec webhook configure
- [ ] Alembic migrations appliquees (`alembic upgrade head`)
- [ ] Flower protege par mot de passe
- [ ] Metriques Prometheus protegees par token
- [ ] Logs centralises configures
- [ ] Backup automatique de la base de donnees
- [ ] CI/CD pipeline fonctionnel
- [ ] Rate limits ajustes pour la charge attendue
