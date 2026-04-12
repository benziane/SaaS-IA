# Auth & Sécurité — SaaS-IA

> Dernière mise à jour : 2026-04-12  
> Version plateforme : v4.4.0

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture auth](#2-architecture-auth)
3. [Modèle utilisateur & rôles](#3-modèle-utilisateur--rôles)
4. [JWT — tokens & cycle de vie](#4-jwt--tokens--cycle-de-vie)
5. [Blacklist & révocation](#5-blacklist--révocation)
6. [Lockout & rate limiting](#6-lockout--rate-limiting)
7. [Email verification guard](#7-email-verification-guard)
8. [Password reset & email verification](#8-password-reset--email-verification)
9. [Frontend — stockage & refresh automatique](#9-frontend--stockage--refresh-automatique)
10. [DEV_MODE — raccourcis développement](#10-dev_mode--raccourcis-développement)
11. [Credentials validés](#11-credentials-validés)
12. [Variables d'environnement](#12-variables-denvironnement)
13. [Endpoints auth](#13-endpoints-auth)
14. [Checklist avant mise en production](#14-checklist-avant-mise-en-production)

---

## 1. Vue d'ensemble

Le système d'authentification est basé sur **JWT stateless** avec :

- Paires **access token (30 min) + refresh token (7 jours)**
- **Rotation obligatoire** des refresh tokens à chaque renouvellement
- **Blacklist JTI** dans Redis pour la révocation individuelle
- **Révocation globale** par timestamp (`logout-all`)
- **Lockout** après 5 tentatives échouées (15 min, fail-closed Redis)
- **Rate limiting** sur tous les endpoints auth
- **Email verification guard** sur 177 endpoints POST/PUT/DELETE (désactivé en `DEV_MODE`)
- **bcrypt** (12 rounds) pour les mots de passe

---

## 2. Architecture auth

```
mvp/backend/app/
├── auth.py                          # Core : JWT, hashing, login, routes /api/auth/*
├── config.py                        # Settings (SECRET_KEY, expiry, dev_mode)
├── models/user.py                   # Modèle User + enum Role
├── schemas/user.py                  # Pydantic schemas (UserCreate, TokenResponse…)
├── core/
│   └── token_blacklist.py           # Blacklist JTI + révocation user via Redis
└── modules/
    └── auth_guards/
        └── middleware.py            # require_verified_email (hard + soft variants)
```

```
mvp/frontend/src/
├── contexts/AuthContext.tsx         # State global (token, user, login/logout)
├── features/auth/
│   ├── api.ts                       # Appels Axios (login, refresh, me, register…)
│   ├── hooks/useAuth.ts             # useCurrentUser() — React Query
│   ├── hooks/useAuthMutations.ts    # useLogin(), useRegister(), useLogout()
│   ├── schemas.ts                   # Validation Zod (loginSchema, registerSchema)
│   └── types.ts                     # Types TS (User, LoginRequest, TokenResponse…)
├── components/guards/AuthGuard.tsx  # HOC protection de routes
├── middleware.ts                    # Next.js middleware — cookie auth_token
└── lib/apiClient.ts                 # Axios interceptors + refresh automatique
```

---

## 3. Modèle utilisateur & rôles

**Fichier :** `mvp/backend/app/models/user.py`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Clé primaire |
| `email` | str (unique, indexed) | Identifiant de connexion |
| `hashed_password` | str | bcrypt 12 rounds |
| `full_name` | str \| None | Nom complet (max 255) |
| `role` | `Role` enum | `admin` \| `manager` \| `user` |
| `is_active` | bool | `True` par défaut — soft delete via ce flag |
| `email_verified` | bool | `False` par défaut — mis à `True` par `/verify-email` |
| `tenant_id` | UUID \| None | FK vers `tenants` pour RLS multi-tenant |
| `created_at` | datetime UTC | Auto |
| `updated_at` | datetime UTC | Auto |

**Rôles disponibles (`Role` enum) :**

| Valeur | Usage |
|--------|-------|
| `admin` | Accès total — système, billing, utilisateurs |
| `manager` | Gestion utilisateurs/workspaces — pas billing/config système |
| `user` | Accès standard aux modules |

---

## 4. JWT — tokens & cycle de vie

**Fichier :** `mvp/backend/app/auth.py`

### Access token

```json
{
  "sub": "user@email.com",
  "tenant_id": "uuid (optionnel)",
  "exp": 1234567890,
  "iat": 1234567800,
  "jti": "uuid-unique-par-token",
  "type": "access"
}
```

- Durée : **30 minutes** (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- Algorithme : HS256
- Signé avec `SECRET_KEY`

### Refresh token

```json
{
  "sub": "user@email.com",
  "exp": future_timestamp,
  "iat": current_timestamp,
  "jti": "uuid-unique",
  "type": "refresh"
}
```

- Durée : **7 jours** (`REFRESH_TOKEN_EXPIRE_DAYS`)
- Rotation : l'ancien est blacklisté immédiatement à chaque `POST /api/auth/refresh`
- Un refresh token utilisé comme access token → 401 (rejet sur `type == "refresh"`)

### Hashing passwords

```python
bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
```

Validation à l'inscription : minimum 8 caractères, au moins 1 lettre + 1 chiffre.

---

## 5. Blacklist & révocation

**Fichier :** `mvp/backend/app/core/token_blacklist.py`

### Révocation individuelle

```
Redis key : token_blacklist:{jti}
TTL       : durée de vie restante du token
```

Utilisé par `POST /api/auth/logout` — révoque le token courant uniquement.

### Révocation globale (logout-all)

```
Redis key : token_blacklist:user:{user_id}
TTL       : 7 jours (= durée max refresh token)
Valeur    : timestamp UNIX de révocation
```

Tout token émis **avant** ce timestamp est refusé (`iat < revocation_timestamp`).  
Utilisé par `POST /api/auth/logout-all` et `PUT /api/auth/password` (change password → révoque tout).

### Comportement Redis down

- Blacklist JTI : **fail-open** (tokens acceptés si Redis indisponible)
- Lockout login : **fail-closed** (429 automatique pendant 30 s si Redis down)

---

## 6. Lockout & rate limiting

**Fichier :** `mvp/backend/app/auth.py` (lignes 36–99)

### Lockout anti-brute-force

| Paramètre | Valeur |
|-----------|--------|
| Max tentatives | 5 |
| Durée lockout | 15 minutes |
| Lockout si Redis down | 30 secondes (fail-closed) |

```
Redis key : login_attempts:{email}
TTL       : 15 minutes (glissant)
```

Réinitialisé automatiquement après connexion réussie.  
Réponse : `429 Too Many Requests` avec `Retry-After` header.

### Rate limiting endpoints

| Endpoint | Limite |
|----------|--------|
| `POST /api/auth/register` | 5 req/min |
| `POST /api/auth/login` | 5 req/min |
| `POST /api/auth/refresh` | 5 req/min |
| `GET /api/auth/me` | 20 req/min |
| `PUT /api/auth/password` | 3 req/min |
| `POST /api/auth/logout` | 10 req/min |
| `POST /api/auth/logout-all` | 3 req/min |
| `POST /api/auth/forgot-password` | 3 req/min |

---

## 7. Email verification guard

**Fichier :** `mvp/backend/app/modules/auth_guards/middleware.py`

```python
async def require_verified_email(current_user: User = Depends(...)) -> User:
    if settings.dev_mode:           # Bypass total en développement
        return current_user
    if not current_user.email_verified:
        raise HTTPException(403, {"code": "EMAIL_NOT_VERIFIED", ...})
    return current_user
```

**Couverture :** 177 endpoints POST/PUT/DELETE sur 35 modules.  
**Variante soft :** `require_verified_email_soft` — passe toujours, sans blocage (pour analytics).

**En production :**
- `email_verified=False` → 403 avec `code: EMAIL_NOT_VERIFIED` et `action: resend_verification`
- Le frontend affiche un banner avec lien de renvoi

**En développement (`DEV_MODE=True`) :**
- Guard bypassé — aucun endpoint ne bloque, même si `email_verified=False`

---

## 8. Password reset & email verification

Deux flows utilisant Redis + SMTP :

### Vérification email

```
POST /api/auth/verify-email   body: { token }
POST /api/auth/resend-verify  body: { email }
```

- Token : 64 hex chars, TTL 24h
- Redis key : `email_verify:{token}` → `user_id`
- Token détruit après usage (single-use)

### Reset mot de passe

```
POST /api/auth/forgot-password  body: { email }
POST /api/auth/reset-password   body: { token, new_password }
```

- Token : 64 hex chars, TTL 1h
- Redis key : `password_reset:{token}` → `user_id`
- Après reset : tous les tokens de l'utilisateur sont révoqués
- En l'absence de SMTP configuré : le lien est loggé dans la console (dev fallback)

---

## 9. Frontend — stockage & refresh automatique

**Fichiers :** `AuthContext.tsx`, `lib/apiClient.ts`

### Stockage dual

| Support | Clé | Usage |
|---------|-----|-------|
| localStorage | `access_token` | Ajouté à chaque requête Axios (`Authorization: Bearer`) |
| localStorage | `refresh_token` | Utilisé par l'interceptor pour renouveler |
| Cookie | `auth_token` | Lu par le middleware Next.js pour la protection SSR |

### Refresh automatique (interceptor Axios)

```
Requête → 401 → Tentative refresh
  ├── Succès : nouveau token stocké, requête originale rejouée
  └── Échec  : localStorage + cookie vidés, redirect /login
```

Mécanisme anti-boucle : flag `isRefreshing` + queue des requêtes en attente.

### Protection des routes

**Middleware Next.js** (`src/middleware.ts`) :
- Vérifie le cookie `auth_token`
- Routes publiques : `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`
- Toutes les autres routes `/dashboard/*` → redirect `/login?redirect=<path>` si non authentifié
- Racine `/` → redirect `/login`

**AuthGuard HOC** (`AuthGuard.tsx`) : second niveau côté client.

---

## 10. DEV_MODE — raccourcis développement

**Activé automatiquement** quand `ENVIRONMENT=development` (valeur par défaut).

**Fichier :** `mvp/backend/app/config.py`

```python
@property
def dev_mode(self) -> bool:
    return self.ENVIRONMENT == "development"
```

| Effet | Détail |
|-------|--------|
| Email verification bypassé | `require_verified_email` passe toujours |
| Users seedés `email_verified=True` | Accès immédiat sans flow email |
| Quick-login panel visible | 3 boutons sur la page login (DEV seulement) |

**Le DEV_MODE est automatiquement désactivé en production** (dès que `ENVIRONMENT=production`).

---

## 11. Credentials validés

### Seed script

**Commande :**
```bash
# Avec Docker
docker exec saas-ia-backend python -m scripts.seed_data

# En local
cd mvp/backend && python -m scripts.seed_data
```

**Résultat :**

| Rôle | Email | Mot de passe (dev) | email_verified |
|------|-------|-------------------|----------------|
| **Admin** | admin@saas-ia.com | `Admin123!` | ✅ True |
| **Manager** | manager@saas-ia.com | `Manager123!` | ✅ True |
| **User** | demo@saas-ia.com | `Demo123!` | ✅ True |

> En production : les mots de passe sont générés aléatoirement (ou via env vars `SEED_ADMIN_PASSWORD`, `SEED_MANAGER_PASSWORD`, `SEED_DEMO_PASSWORD`).

### Quick-login page

Sur `http://localhost:3002/login` en mode développement, 3 boutons apparaissent :

```
[ADMIN]   admin@saas-ia.com
[MANAGER] manager@saas-ia.com
[USER]    demo@saas-ia.com
```

Ces boutons appellent le même flow que le formulaire (`loginMutation.mutateAsync()`).

---

## 12. Variables d'environnement

**Fichier :** `mvp/backend/.env.example`

| Variable | Défaut | Description |
|----------|--------|-------------|
| `SECRET_KEY` | *(requis)* | Clé de signature JWT — min 32 chars aléatoires |
| `ALGORITHM` | `HS256` | Algorithme JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Durée access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Durée refresh token |
| `ENVIRONMENT` | `development` | `development` ou `production` |
| `SEED_ADMIN_PASSWORD` | `Admin123!` en dev | Mot de passe admin seedé |
| `SEED_MANAGER_PASSWORD` | `Manager123!` en dev | Mot de passe manager seedé |
| `SEED_DEMO_PASSWORD` | `Demo123!` en dev | Mot de passe user seedé |
| `SMTP_HOST` | `` | Serveur SMTP (Mailpit en dev : `localhost`) |
| `SMTP_PORT` | `587` | Port SMTP |
| `SMTP_USER` | `` | Identifiant SMTP |
| `SMTP_PASSWORD` | `` | Mot de passe SMTP |
| `SMTP_FROM` | `noreply@saas-ia.com` | Expéditeur des emails |
| `FRONTEND_URL` | `http://localhost:3002` | Utilisé dans les liens email |
| `REDIS_URL` | `` | Redis pour blacklist + lockout |

> **Mailpit** disponible sur `http://localhost:8025` — interface email pour dev (port SMTP 1025).

---

## 13. Endpoints auth

**Base URL :** `POST|GET /api/auth/`

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| POST | `/register` | Non | Créer un compte |
| POST | `/login` | Non | Login OAuth2 form → `TokenResponse` |
| POST | `/refresh` | Non | Renouveler les tokens (rotation) |
| GET | `/me` | ✅ | Profil utilisateur courant |
| PUT | `/profile` | ✅ | Mettre à jour `full_name` |
| PUT | `/password` | ✅ | Changer le mot de passe (révoque tous les tokens) |
| POST | `/logout` | ✅ | Révoquer le token courant |
| POST | `/logout-all` | ✅ | Révoquer tous les tokens de l'utilisateur |
| POST | `/forgot-password` | Non | Demander un lien de reset |
| POST | `/reset-password` | Non | Appliquer un nouveau mot de passe |
| POST | `/verify-email` | Non | Valider un token d'email |
| POST | `/resend-verify` | Non | Renvoyer l'email de vérification |
| POST | `/test-email` | ✅ Admin | Tester la config SMTP |

**Format login (OAuth2 form-urlencoded) :**
```
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@saas-ia.com&password=Admin123!
```

**Réponse `TokenResponse` :**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 14. Checklist avant mise en production

- [ ] `SECRET_KEY` changé pour une valeur forte aléatoire (min 32 chars) — `openssl rand -hex 32`
- [ ] `ENVIRONMENT=production` dans le `.env`
- [ ] `SEED_ADMIN_PASSWORD`, `SEED_MANAGER_PASSWORD`, `SEED_DEMO_PASSWORD` définis (ou supprimés si pas de seed)
- [ ] SMTP configuré (ou désactivé explicitement)
- [ ] `FRONTEND_URL` pointe sur le domaine de production
- [ ] Redis accessible (lockout + blacklist actifs)
- [ ] `CORS_ORIGINS` restreint au(x) domaine(s) de production
- [ ] `TRUSTED_PROXIES` configuré si reverse-proxy (nginx, Cloudflare…)
- [ ] Vérifier que `DEV_MODE` est bien `False` : `python -c "from app.config import settings; assert not settings.dev_mode"`
- [ ] Supprimer ou désactiver les endpoints de test (`/api/auth/test-email` en dehors d'admin)
- [ ] S'assurer que le script seed ne tourne PAS automatiquement au démarrage

---

*Document généré à partir de l'audit du code source — `mvp/backend/app/auth.py`, `config.py`, `models/user.py`, `core/token_blacklist.py`, `modules/auth_guards/middleware.py`, `scripts/seed_data.py`, et des fichiers frontend correspondants.*
