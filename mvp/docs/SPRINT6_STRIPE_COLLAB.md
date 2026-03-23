# Sprint 6 : Stripe Integration + Collaboration Workspaces

**Date** : 2026-03-23
**Version** : MVP 2.6.0
**Statut** : Termine

---

## 1. Integration Stripe

### Architecture

```
Frontend (/billing)              Backend                       Stripe
      |                               |                          |
      |-- POST /billing/checkout ---->|                          |
      |   {plan_name: "pro"}          |-- checkout.create() ---->|
      |                               |<-- checkout_url ---------|
      |<-- redirect to Stripe --------|                          |
      |                               |                          |
      | (user pays)                   |<-- webhook --------------|
      |                               |  checkout.session.completed
      |                               |  -> upgrade plan_id       |
      |                               |  -> save subscription_id  |
      |                               |                          |
      |-- POST /billing/portal ------>|                          |
      |                               |-- billing_portal ------->|
      |<-- redirect ------------------|                          |
```

### Backend

**Configuration** (`app/config.py`) :
- `STRIPE_SECRET_KEY` : Cle secrete Stripe
- `STRIPE_WEBHOOK_SECRET` : Secret de verification webhook
- `STRIPE_PRICE_PRO_MONTHLY` : Price ID Stripe pour le plan Pro

**Service** (`app/modules/billing/stripe_service.py`) :
- `create_checkout_session()` : Cree session Stripe Checkout, cree Stripe Customer si besoin
- `create_portal_session()` : Ouvre portail de gestion abonnement
- `handle_webhook()` : Verifie signature, dispatche events
- `_handle_checkout_completed()` : Met a jour plan_id et subscription_id
- `_handle_subscription_deleted()` : Downgrade vers Free

**Champs ajoutes** :
- `plans.stripe_price_id` : Lien vers le Price Stripe
- `user_quotas.stripe_customer_id` : ID client Stripe
- `user_quotas.stripe_subscription_id` : ID abonnement Stripe

**Endpoints** :

| Methode | Endpoint | Description | Auth | Rate Limit |
|---------|----------|-------------|------|------------|
| POST | /api/billing/checkout | Creer session Stripe Checkout | Oui | 5/min |
| POST | /api/billing/portal | Ouvrir portail de gestion | Oui | 5/min |
| POST | /api/billing/webhook | Webhook Stripe | Signature | - |

### Frontend

- Bouton "Upgrade to Pro" sur chaque plan non-actuel
- Bouton "Manage Subscription" pour les abonnes payants
- Alertes `?success=true` / `?canceled=true` apres retour Stripe
- Hooks : `useCheckout()`, `usePortal()`

---

## 2. Collaboration Workspaces

### Architecture

```
Frontend (/workspaces)           Backend
      |                               |
      |-- POST /workspaces ---------> | create workspace + owner member
      |<-- {workspace} --------------|
      |                               |
      |-- POST /{id}/invite --------> | lookup user by email
      |   {email, role}               | create WorkspaceMember
      |<-- {member} -----------------|
      |                               |
      |-- POST /{id}/share ---------->| create SharedItem
      |   {item_type, item_id}        |
      |                               |
      |-- POST /items/{id}/comments ->| create Comment
      |   {content}                   |
```

### Backend

**Modeles** (`app/models/workspace.py`) :

| Table | Champs cles |
|-------|-------------|
| workspaces | name, description, owner_id, is_active |
| workspace_members | workspace_id, user_id, role (owner/editor/viewer) |
| shared_items | workspace_id, item_type, item_id, shared_by |
| comments | shared_item_id, user_id, content |

**Service** (`app/modules/workspaces/service.py`) :
- CRUD workspaces (owner-based access)
- Invite / remove members par email
- Share items (transcription, pipeline, document)
- Comments CRUD sur shared items
- Member count

**Endpoints** (12 au total) :

| Methode | Endpoint | Description | Rate |
|---------|----------|-------------|------|
| POST | / | Creer workspace | 10/min |
| GET | / | Lister workspaces | 20/min |
| GET | /{id} | Detail workspace | 30/min |
| PUT | /{id} | Modifier (owner) | 10/min |
| DELETE | /{id} | Supprimer (owner) | 5/min |
| POST | /{id}/invite | Inviter membre | 10/min |
| GET | /{id}/members | Lister membres | 20/min |
| DELETE | /{id}/members/{uid} | Retirer membre | 10/min |
| POST | /{id}/share | Partager item | 10/min |
| GET | /{id}/items | Lister items | 20/min |
| POST | /items/{id}/comments | Commenter | 20/min |
| GET | /items/{id}/comments | Lister commentaires | 30/min |

### Frontend

**Page** : `/workspaces` (`src/app/(dashboard)/workspaces/page.tsx`)
- Grille de cartes workspace (nom, description, member count)
- Selection workspace -> panneau membres a droite
- Dialog creation workspace (nom + description)
- Dialog invitation membre (email + role)
- Role chips colores (owner=primary, editor=success, viewer=default)

---

## 3. Migrations Alembic

| Revision | Description |
|----------|-------------|
| stripe_001 | Ajout colonnes Stripe (stripe_price_id, stripe_customer_id, stripe_subscription_id) |
| collab_001 | 4 tables workspace (workspaces, workspace_members, shared_items, comments) |

---

## 4. Dependances ajoutees

| Package | Version | Usage |
|---------|---------|-------|
| stripe | 8.0.0 | Paiement, checkout, webhooks |
| aiosqlite | 0.19.0 | Tests d'integration SQLite async |

---

## 5. Nouvelle page frontend

| Route | Description |
|-------|-------------|
| /workspaces | Collaboration workspaces |

**Navigation mise a jour** :
```
Dashboard
AI Modules
  Transcription
  Chat IA
  Compare
  Pipelines
  Knowledge Base
Platform
  Modules
  API & Keys
  Workspaces          <-- NOUVEAU
Account
  Profile
  Billing (+ Stripe)  <-- MIS A JOUR
```
