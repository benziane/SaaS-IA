# 🗺️ ROADMAP - SaaS-IA MVP

**Date** : 2025-11-14  
**Version Actuelle** : MVP 1.0.0 (Grade S++ 94/100)  
**Objectif** : Version Production 2.0.0 (Grade S++ 98/100)

---

## 📋 VUE D'ENSEMBLE

Cette roadmap détaille **tout ce qu'il reste à faire** pour passer du MVP actuel à une version production complète et robuste.

### Priorités
- 🔴 **CRITIQUE** : Bloquant pour production
- 🟡 **IMPORTANT** : Nécessaire pour qualité production
- 🟢 **SOUHAITABLE** : Amélioration expérience
- 🔵 **FUTUR** : Évolution long terme

---

## 🔴 PHASE 1 : CRITIQUES PRODUCTION (2-3 semaines)

### 1.1 Tests Automatisés (🔴 CRITIQUE)

**Problème** : Coverage 0%, aucun test automatisé  
**Impact** : Risque de régression, pas de CI/CD fiable  
**Temps estimé** : 1 semaine

#### Backend Tests

**À implémenter** :

```python
# tests/test_auth.py
@pytest.mark.asyncio
async def test_register_user():
    """Test user registration"""
    # Test création utilisateur
    # Test email déjà existant
    # Test validation password

@pytest.mark.asyncio
async def test_login():
    """Test login flow"""
    # Test login valide
    # Test login invalide
    # Test rate limiting

@pytest.mark.asyncio
async def test_jwt_token():
    """Test JWT token"""
    # Test génération token
    # Test validation token
    # Test expiration token

# tests/test_transcription.py
@pytest.mark.asyncio
async def test_create_transcription():
    """Test transcription creation"""
    # Test création job
    # Test mode MOCK
    # Test validation URL

@pytest.mark.asyncio
async def test_transcription_status():
    """Test transcription status"""
    # Test récupération status
    # Test mise à jour status
    # Test erreurs
```

**Objectif Coverage** : ≥ 85%

**Commandes** :
```bash
cd backend
pytest --cov=app --cov-report=html --cov-report=term
pytest --cov-fail-under=85
```

#### Frontend Tests

**À implémenter** :

```typescript
// src/features/auth/__tests__/useAuth.test.tsx
describe('useAuth', () => {
  it('should login successfully', async () => {
    // Test login
  });
  
  it('should handle login error', async () => {
    // Test erreur login
  });
  
  it('should logout successfully', async () => {
    // Test logout
  });
});

// src/features/auth/__tests__/LoginPage.test.tsx
describe('LoginPage', () => {
  it('should render login form', () => {
    // Test rendu
  });
  
  it('should validate form inputs', async () => {
    // Test validation
  });
  
  it('should submit form', async () => {
    // Test soumission
  });
});

// src/tests/e2e/auth.spec.ts (Playwright)
test('complete auth flow', async ({ page }) => {
  // Test E2E complet
  await page.goto('http://localhost:3002/login');
  await page.fill('[name="email"]', 'test@test.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```

**Objectif Coverage** : ≥ 85%

**Commandes** :
```bash
cd frontend
npm test -- --coverage
npm run test:e2e
```

**Livrables** :
- [ ] Tests unitaires backend (≥85% coverage)
- [ ] Tests unitaires frontend (≥85% coverage)
- [ ] Tests E2E (scénarios critiques)
- [ ] Tests accessibilité (axe-core)
- [ ] CI/CD avec tests automatiques

---

### 1.2 Configuration Production (🔴 CRITIQUE)

**Problème** : Configuration dev hardcodée  
**Impact** : Failles sécurité, pas prêt pour déploiement  
**Temps estimé** : 2-3 jours

#### Backend

**À faire** :

```python
# app/config.py
class Settings(BaseSettings):
    # ❌ AVANT
    SECRET_KEY: str = "change-me-in-production-use-strong-random-key"
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:3002,http://localhost:8004"
    
    # ✅ APRÈS
    SECRET_KEY: str = Field(..., min_length=32)  # Obligatoire
    DEBUG: bool = Field(default=False)  # False par défaut
    CORS_ORIGINS: str = Field(...)  # Obligatoire
    ENVIRONMENT: str = Field(default="production")
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if v == "change-me-in-production-use-strong-random-key":
            raise ValueError("SECRET_KEY must be changed in production")
        return v
```

**Variables d'environnement production** :
```bash
# .env.production
SECRET_KEY=<généré avec openssl rand -hex 32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql://user:pass@prod-db:5432/saas_ia
REDIS_URL=redis://prod-redis:6379
ASSEMBLYAI_API_KEY=<clé réelle>
CORS_ORIGINS=https://app.saas-ia.com
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=WARNING
```

#### Frontend

**À faire** :

```typescript
// Cookie avec flag Secure + HttpOnly
document.cookie = `auth_token=${token}; path=/; max-age=1800; SameSite=Strict; Secure`;

// next.config.ts - Headers sécurité renforcés
headers: [
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' },
  { key: 'Content-Security-Policy', value: "default-src 'self'; ..." }
]
```

**Variables d'environnement production** :
```bash
# .env.production
NEXT_PUBLIC_API_URL=https://api.saas-ia.com
NODE_ENV=production
```

**Livrables** :
- [ ] SECRET_KEY obligatoire et validée
- [ ] DEBUG=False par défaut
- [ ] CORS restreint au domaine production
- [ ] Cookies avec flags Secure + HttpOnly
- [ ] CSP (Content Security Policy)
- [ ] HTTPS uniquement
- [ ] Variables d'environnement documentées

---

### 1.3 Gestion Utilisateur Admin Test (🔴 CRITIQUE)

**Problème** : Utilisateur `admin@saas-ia.com` / `admin123` en base  
**Impact** : Faille sécurité majeure en production  
**Temps estimé** : 1 jour

**À faire** :

1. **Script de nettoyage** :
```sql
-- scripts/cleanup_test_users.sql
DELETE FROM transcriptions WHERE user_id IN (
  SELECT id FROM users WHERE email LIKE '%@saas-ia.com'
);
DELETE FROM users WHERE email LIKE '%@saas-ia.com';
```

2. **Script création admin production** :
```python
# scripts/create_admin_prod.py
import getpass
import asyncio
from app.auth import get_password_hash
from app.database import get_session
from app.models.user import User, Role

async def create_admin():
    email = input("Admin email: ")
    password = getpass.getpass("Admin password (min 12 chars): ")
    full_name = input("Full name: ")
    
    if len(password) < 12:
        print("Password must be at least 12 characters")
        return
    
    hashed = get_password_hash(password)
    
    async with get_session() as session:
        admin = User(
            email=email,
            hashed_password=hashed,
            full_name=full_name,
            role=Role.ADMIN,
            is_active=True
        )
        session.add(admin)
        await session.commit()
        print(f"Admin created: {email}")

if __name__ == "__main__":
    asyncio.run(create_admin())
```

3. **Désactiver Quick Login en production** :
```typescript
// login/page.tsx
{process.env.NODE_ENV === 'development' && (
  // Quick Login visible uniquement en dev
)}
```

**Livrables** :
- [ ] Script suppression utilisateurs test
- [ ] Script création admin production sécurisé
- [ ] Quick Login désactivé en production
- [ ] Documentation procédure création admin

---

### 1.4 Logs Sensibles (🔴 CRITIQUE)

**Problème** : Logs peuvent contenir données sensibles  
**Impact** : Fuite d'informations, non-conformité RGPD  
**Temps estimé** : 2 jours

**À faire** :

```python
# app/logging.py
import structlog
from typing import Any

def mask_sensitive_data(logger, method_name, event_dict):
    """Masquer données sensibles dans les logs"""
    sensitive_keys = ['password', 'token', 'secret', 'api_key']
    
    for key in sensitive_keys:
        if key in event_dict:
            event_dict[key] = '***MASKED***'
    
    return event_dict

structlog.configure(
    processors=[
        mask_sensitive_data,  # Masquer données sensibles
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ]
)
```

**Livrables** :
- [ ] Masquage automatique données sensibles
- [ ] Logs structurés JSON (production)
- [ ] Rotation logs (logrotate)
- [ ] Rétention logs (30 jours max)

---

## 🟡 PHASE 2 : IMPORTANT QUALITÉ (3-4 semaines)

### 2.1 Refresh Tokens (🟡 IMPORTANT)

**Problème** : Token expire après 30 min, utilisateur déconnecté  
**Impact** : UX dégradée, frustration utilisateur  
**Temps estimé** : 3-4 jours

**À implémenter** :

```python
# app/models/user.py
class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    is_revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# app/auth.py
def create_refresh_token(user_id: UUID) -> str:
    """Créer refresh token (7 jours)"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    # Stocker en DB
    return token

@router.post("/refresh")
async def refresh_access_token(refresh_token: str):
    """Rafraîchir access token"""
    # Vérifier refresh token
    # Générer nouveau access token
    # Retourner nouveau access token
```

**Livrables** :
- [ ] Table `refresh_tokens` en DB
- [ ] Endpoint `/auth/refresh`
- [ ] Rotation automatique côté frontend
- [ ] Révocation tokens (logout)
- [ ] Tests refresh flow

---

### 2.2 Cache Redis Avancé (🟡 IMPORTANT)

**Problème** : Redis installé mais non utilisé  
**Impact** : Performance sous-optimale, coûts API élevés  
**Temps estimé** : 2-3 jours

**À implémenter** :

```python
# app/cache.py
import redis.asyncio as redis
from functools import wraps
import json

redis_client = redis.from_url(settings.REDIS_URL)

def cache(ttl: int = 300):
    """Décorateur cache Redis"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Générer clé cache
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Vérifier cache
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Exécuter fonction
            result = await func(*args, **kwargs)
            
            # Stocker en cache
            await redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator

# Usage
@cache(ttl=3600)  # Cache 1 heure
async def get_transcription(transcription_id: UUID):
    # Récupérer transcription
    return transcription
```

**Stratégie cache** :

| Donnée | TTL | Raison |
|--------|-----|--------|
| Transcriptions complétées | 1 heure | Rarement modifiées |
| User profile | 15 min | Peut changer |
| Liste transcriptions | 5 min | Souvent mise à jour |
| Stats dashboard | 10 min | Calculs coûteux |

**Livrables** :
- [ ] Décorateur cache Redis
- [ ] Cache transcriptions complétées
- [ ] Cache profil utilisateur
- [ ] Invalidation cache intelligente
- [ ] Monitoring cache (hit rate)

---

### 2.3 Monitoring & Observabilité (🟡 IMPORTANT)

**Problème** : Pas de monitoring, pas d'alertes  
**Impact** : Détection problèmes tardive, debugging difficile  
**Temps estimé** : 1 semaine

**À implémenter** :

#### Prometheus + Grafana

```python
# app/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Métriques HTTP
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Métriques métier
transcriptions_total = Counter(
    'transcriptions_total',
    'Total transcriptions',
    ['status']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

# Middleware
@app.middleware("http")
async def prometheus_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    http_request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

**Dashboard Grafana** :
- Requêtes HTTP (rate, latence, erreurs)
- Transcriptions (total, par statut, durée)
- Utilisateurs (actifs, inscriptions, logins)
- Base de données (connexions, queries, latence)
- Redis (hit rate, mémoire, connexions)

#### Logs Centralisés (ELK ou CloudWatch)

```yaml
# docker-compose.yml
services:
  elasticsearch:
    image: elasticsearch:8.11.0
    
  logstash:
    image: logstash:8.11.0
    
  kibana:
    image: kibana:8.11.0
```

**Livrables** :
- [ ] Prometheus metrics endpoint
- [ ] Grafana dashboards
- [ ] Alertes (email/Slack)
- [ ] Logs centralisés (ELK/CloudWatch)
- [ ] Tracing distribué (optionnel)

---

### 2.4 CI/CD Complet (🟡 IMPORTANT)

**Problème** : CI/CD basique, pas de déploiement auto  
**Impact** : Déploiements manuels, risque erreurs  
**Temps estimé** : 1 semaine

**À implémenter** :

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install poetry
          poetry install
      - name: Run tests
        run: |
          cd backend
          poetry run pytest --cov=app --cov-fail-under=85
      - name: Upload coverage
        uses: codecov/codecov-action@v3
  
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage
      - name: Run E2E tests
        run: |
          cd frontend
          npm run test:e2e
  
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
      - name: Run Bandit
        run: |
          cd backend
          poetry run bandit -r app/
  
  deploy-staging:
    needs: [backend-tests, frontend-tests, security-scan]
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: |
          # Déploiement staging
  
  deploy-production:
    needs: [backend-tests, frontend-tests, security-scan]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          # Déploiement production
```

**Livrables** :
- [ ] Tests automatiques sur PR
- [ ] Scan sécurité (Trivy, Bandit)
- [ ] Déploiement auto staging (develop)
- [ ] Déploiement auto production (main)
- [ ] Rollback automatique si erreur

---

### 2.5 Documentation API Améliorée (🟡 IMPORTANT)

**Problème** : Swagger basique, pas d'exemples  
**Impact** : Intégration difficile pour développeurs  
**Temps estimé** : 2-3 jours

**À améliorer** :

```python
# app/auth.py
@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="""
    Register a new user account.
    
    **Rate limit**: 5 requests/minute
    
    **Requirements**:
    - Email must be valid and unique
    - Password must be at least 8 characters
    - Full name is optional
    
    **Returns**:
    - 201: User created successfully
    - 400: Email already registered or validation error
    - 429: Rate limit exceeded
    """,
    responses={
        201: {
            "description": "User created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "user@example.com",
                        "full_name": "John Doe",
                        "role": "user",
                        "is_active": true,
                        "created_at": "2025-01-01T00:00:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Email already registered",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already registered"
                    }
                }
            }
        }
    }
)
async def register(...):
    ...
```

**Livrables** :
- [ ] Descriptions complètes endpoints
- [ ] Exemples requêtes/réponses
- [ ] Codes erreurs documentés
- [ ] Guide démarrage rapide
- [ ] Collection Postman/Insomnia

---

## 🟢 PHASE 3 : AMÉLIORATIONS UX (2-3 semaines)

### 3.1 Dashboard Riche (🟢 SOUHAITABLE)

**Objectif** : Dashboard avec statistiques et graphiques  
**Temps estimé** : 1 semaine

**À implémenter** :

```typescript
// dashboard/page.tsx
<Grid container spacing={3}>
  {/* Stats Cards */}
  <Grid item xs={12} sm={6} md={3}>
    <StatsCard
      title="Total Transcriptions"
      value={stats.total}
      icon={<TranscriptIcon />}
      trend="+12%"
    />
  </Grid>
  
  {/* Graphiques */}
  <Grid item xs={12} md={8}>
    <Chart
      type="line"
      data={transcriptionsOverTime}
      title="Transcriptions Over Time"
    />
  </Grid>
  
  {/* Recent Activity */}
  <Grid item xs={12} md={4}>
    <RecentActivity activities={recentActivities} />
  </Grid>
</Grid>
```

**Livrables** :
- [ ] Stats cards (total, pending, completed, failed)
- [ ] Graphiques (Chart.js ou Recharts)
- [ ] Activité récente
- [ ] Filtres temporels (jour, semaine, mois)

---

### 3.2 Notifications en Temps Réel (🟢 SOUHAITABLE)

**Objectif** : Notifier utilisateur quand transcription terminée  
**Temps estimé** : 3-4 jours

**À implémenter** :

```python
# app/websocket.py
from fastapi import WebSocket

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: UUID):
    await websocket.accept()
    
    # Écouter événements transcription
    async for message in redis_pubsub:
        if message['user_id'] == user_id:
            await websocket.send_json({
                "type": "transcription_completed",
                "data": message['data']
            })
```

```typescript
// frontend - useWebSocket.ts
export function useWebSocket(userId: string) {
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8004/ws/${userId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'transcription_completed') {
        toast.success('Transcription completed!');
        queryClient.invalidateQueries(['transcriptions']);
      }
    };
    
    return () => ws.close();
  }, [userId]);
}
```

**Livrables** :
- [ ] WebSocket endpoint backend
- [ ] Hook useWebSocket frontend
- [ ] Notifications toast
- [ ] Reconnexion automatique

---

### 3.3 Profil Utilisateur (🟢 SOUHAITABLE)

**Objectif** : Page profil avec édition infos  
**Temps estimé** : 2-3 jours

**À implémenter** :

```typescript
// profile/page.tsx
<Card>
  <CardHeader>
    <Avatar src={user.avatar} />
    <Typography variant="h5">{user.full_name}</Typography>
  </CardHeader>
  
  <CardContent>
    <Form onSubmit={handleUpdate}>
      <TextField
        label="Full Name"
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
      />
      
      <TextField
        label="Email"
        value={user.email}
        disabled
      />
      
      <Button type="submit">Update Profile</Button>
    </Form>
    
    <Divider />
    
    <Typography variant="h6">Change Password</Typography>
    <Form onSubmit={handlePasswordChange}>
      <TextField
        type="password"
        label="Current Password"
      />
      <TextField
        type="password"
        label="New Password"
      />
      <Button type="submit">Change Password</Button>
    </Form>
  </CardContent>
</Card>
```

**Livrables** :
- [ ] Page profil utilisateur
- [ ] Édition nom/email
- [ ] Changement mot de passe
- [ ] Upload avatar (optionnel)
- [ ] Historique activité

---

### 3.4 Pagination & Filtres (🟢 SOUHAITABLE)

**Objectif** : Pagination et filtres sur liste transcriptions  
**Temps estimé** : 2 jours

**À implémenter** :

```python
# app/modules/transcription/routes.py
@router.get("/", response_model=PaginatedResponse[TranscriptionRead])
async def list_transcriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[TranscriptionStatus] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|status)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Filtrage + tri + pagination
    query = select(Transcription).where(Transcription.user_id == current_user.id)
    
    if status:
        query = query.where(Transcription.status == status)
    
    if search:
        query = query.where(Transcription.video_url.ilike(f"%{search}%"))
    
    if sort_order == "desc":
        query = query.order_by(desc(getattr(Transcription, sort_by)))
    else:
        query = query.order_by(asc(getattr(Transcription, sort_by)))
    
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

**Livrables** :
- [ ] Pagination backend
- [ ] Filtres (status, search)
- [ ] Tri (date, status)
- [ ] Composant Pagination frontend
- [ ] Composant Filtres frontend

---

## 🔵 PHASE 4 : ÉVOLUTIONS LONG TERME (3-6 mois)

### 4.1 Nouveaux Modules IA (🔵 FUTUR)

**Objectif** : Ajouter modules IA supplémentaires  
**Temps estimé** : 2-3 semaines par module

**Modules proposés** :

1. **Génération de Texte** (GPT-4, Claude)
   - Génération articles, emails, résumés
   - Templates personnalisables
   - Export formats multiples

2. **Analyse de Sentiment** (HuggingFace)
   - Analyse texte/tweets/reviews
   - Score sentiment (positif/négatif/neutre)
   - Visualisation graphique

3. **Traduction** (DeepL, Google Translate)
   - Traduction multi-langues
   - Détection langue automatique
   - Glossaire personnalisé

4. **Génération d'Images** (DALL-E, Midjourney)
   - Génération images depuis prompt
   - Variations d'images
   - Galerie images générées

5. **OCR** (Tesseract, Google Vision)
   - Extraction texte depuis images
   - Support PDF
   - Export formats multiples

**Architecture modulaire** :
```python
# app/modules/text_generation/
├── __init__.py
├── routes.py
├── service.py
├── models.py
└── schemas.py
```

---

### 4.2 Système de Crédits (🔵 FUTUR)

**Objectif** : Monétisation avec système de crédits  
**Temps estimé** : 2-3 semaines

**À implémenter** :

```python
# app/models/billing.py
class CreditPack(SQLModel, table=True):
    id: UUID
    name: str  # "Starter", "Pro", "Enterprise"
    credits: int
    price: Decimal
    
class UserCredit(SQLModel, table=True):
    id: UUID
    user_id: UUID
    credits_remaining: int
    credits_used: int
    
class CreditTransaction(SQLModel, table=True):
    id: UUID
    user_id: UUID
    amount: int  # Positif = achat, négatif = utilisation
    type: str  # "purchase", "usage", "refund"
    module: str  # "transcription", "generation", etc.
    created_at: datetime
```

**Tarification** :
- Transcription : 1 crédit / minute
- Génération texte : 1 crédit / 1000 tokens
- Traduction : 1 crédit / 1000 caractères
- etc.

---

### 4.3 Multi-Tenancy (🔵 FUTUR)

**Objectif** : Support organisations avec équipes  
**Temps estimé** : 1 mois

**À implémenter** :

```python
# app/models/organization.py
class Organization(SQLModel, table=True):
    id: UUID
    name: str
    plan: str  # "free", "pro", "enterprise"
    
class OrganizationMember(SQLModel, table=True):
    id: UUID
    organization_id: UUID
    user_id: UUID
    role: str  # "owner", "admin", "member"
    
# Tous les models ajoutent:
class Transcription(SQLModel, table=True):
    # ...
    organization_id: Optional[UUID]  # Nouveau champ
```

---

### 4.4 API Publique (🔵 FUTUR)

**Objectif** : API publique pour intégrations tierces  
**Temps estimé** : 3-4 semaines

**À implémenter** :

```python
# app/api_keys.py
class APIKey(SQLModel, table=True):
    id: UUID
    user_id: UUID
    key: str  # Hash de la clé
    name: str
    permissions: List[str]  # ["transcription:read", "transcription:write"]
    rate_limit: int  # Requêtes/jour
    expires_at: Optional[datetime]
    
# Middleware
async def verify_api_key(api_key: str = Header(...)):
    # Vérifier clé API
    # Vérifier permissions
    # Vérifier rate limit
```

**Documentation** :
- OpenAPI spec publique
- SDK Python/JavaScript
- Exemples d'intégration
- Webhooks

---

## 📊 RÉCAPITULATIF PRIORITÉS

### Par Urgence

| Phase | Priorité | Temps | Statut |
|-------|----------|-------|--------|
| **Phase 1 : Critiques** | 🔴 | 2-3 sem | À faire |
| Tests automatisés | 🔴 | 1 sem | À faire |
| Config production | 🔴 | 2-3 j | À faire |
| Admin test cleanup | 🔴 | 1 j | À faire |
| Logs sensibles | 🔴 | 2 j | À faire |
| **Phase 2 : Important** | 🟡 | 3-4 sem | À faire |
| Refresh tokens | 🟡 | 3-4 j | À faire |
| Cache Redis | 🟡 | 2-3 j | À faire |
| Monitoring | 🟡 | 1 sem | À faire |
| CI/CD complet | 🟡 | 1 sem | À faire |
| Doc API | 🟡 | 2-3 j | À faire |
| **Phase 3 : UX** | 🟢 | 2-3 sem | À faire |
| Dashboard riche | 🟢 | 1 sem | À faire |
| Notifications RT | 🟢 | 3-4 j | À faire |
| Profil utilisateur | 🟢 | 2-3 j | À faire |
| Pagination/filtres | 🟢 | 2 j | À faire |
| **Phase 4 : Long terme** | 🔵 | 3-6 mois | Futur |
| Nouveaux modules IA | 🔵 | Variable | Futur |
| Système crédits | 🔵 | 2-3 sem | Futur |
| Multi-tenancy | 🔵 | 1 mois | Futur |
| API publique | 🔵 | 3-4 sem | Futur |

### Par Impact

**Impact Critique (Bloquant Production)** :
1. Tests automatisés (Coverage 0% → 85%)
2. Configuration production (Sécurité)
3. Admin test cleanup (Faille sécurité)
4. Logs sensibles (RGPD)

**Impact Important (Qualité Production)** :
5. Refresh tokens (UX)
6. Cache Redis (Performance)
7. Monitoring (Observabilité)
8. CI/CD complet (Fiabilité)

**Impact Souhaitable (Amélioration)** :
9. Dashboard riche (UX)
10. Notifications temps réel (UX)
11. Profil utilisateur (Fonctionnalité)
12. Pagination/filtres (UX)

---

## 🎯 OBJECTIFS PAR MILESTONE

### Milestone 1 : Production-Ready (1 mois)
**Objectif** : Déploiement production sécurisé

**Checklist** :
- [ ] Tests automatisés (≥85% coverage)
- [ ] Configuration production validée
- [ ] Admin test supprimé
- [ ] Logs sensibles masqués
- [ ] Refresh tokens implémentés
- [ ] Monitoring actif
- [ ] CI/CD complet
- [ ] Documentation API complète

**Grade cible** : S++ (98/100)

---

### Milestone 2 : UX Améliorée (2 mois)
**Objectif** : Expérience utilisateur optimale

**Checklist** :
- [ ] Dashboard avec stats
- [ ] Notifications temps réel
- [ ] Profil utilisateur éditable
- [ ] Pagination et filtres
- [ ] Cache Redis optimisé
- [ ] Performance optimisée

**Grade cible** : S++ (99/100)

---

### Milestone 3 : Évolution (6 mois)
**Objectif** : Plateforme multi-modules mature

**Checklist** :
- [ ] 3+ modules IA supplémentaires
- [ ] Système de crédits
- [ ] Multi-tenancy
- [ ] API publique
- [ ] SDK Python/JS
- [ ] Webhooks

**Grade cible** : S++ (100/100)

---

## 📞 CONTACT & CONTRIBUTION

Pour toute question ou suggestion sur cette roadmap :
- **Issues** : https://github.com/benziane/SaaS-IA/issues
- **Discussions** : https://github.com/benziane/SaaS-IA/discussions

---

**Roadmap maintenue par** : Assistant IA  
**Dernière mise à jour** : 2025-11-14  
**Version** : 1.0.0  
**Statut** : ✅ À JOUR

