---
name: security-audit
description: |
  Skill pour l'audit de securite du projet SaaS-IA.
  TRIGGER quand: l'utilisateur mentionne "securite", "audit", "vulnerabilite", "OWASP",
  ou lors de review de code sensible (authentification, paiement Stripe, gestion de secrets).
  Ce skill opere en mode READ-ONLY.
---

# Audit de Securite - SaaS-IA

## Mode: READ-ONLY
Ce skill analyse le code sans le modifier. Il produit un rapport avec des recommandations.

## Checklist OWASP Top 10

### A01 - Broken Access Control
- [ ] Tous les endpoints proteges utilisent `Depends(get_current_user)`
- [ ] Verification des roles (Role.ADMIN, Role.USER) sur les endpoints sensibles
- [ ] Pas d'IDOR (Insecure Direct Object Reference) - verifier que l'user a acces a la ressource

### A02 - Cryptographic Failures
- [ ] Secrets dans `.env` uniquement (pas en dur dans le code)
- [ ] JWT signe avec cle secrete forte (`SECRET_KEY`)
- [ ] Mots de passe hashes avec bcrypt (passlib)
- [ ] HTTPS en production

### A03 - Injection
- [ ] SQLModel/SQLAlchemy avec requetes parametrees (pas de SQL brut)
- [ ] Validation Pydantic sur toutes les entrees
- [ ] Pas de `eval()`, `exec()`, ou `os.system()` avec des entrees utilisateur

### A04 - Insecure Design
- [ ] Rate limiting active sur tous les endpoints publics (slowapi)
- [ ] Pagination sur les endpoints de liste
- [ ] Limites de taille sur les uploads

### A05 - Security Misconfiguration
- [ ] CORS configure restrictivement (`CORS_ORIGINS` dans settings)
- [ ] Headers de securite (X-Content-Type-Options, X-Frame-Options)
- [ ] Mode DEBUG desactive en production

### A07 - Authentication Failures
- [ ] JWT avec expiration (ACCESS_TOKEN_EXPIRE_MINUTES)
- [ ] Refresh token avec rotation
- [ ] Brute force protection (rate limiting sur /auth/login)

### A08 - Data Integrity Failures
- [ ] Webhooks Stripe verifies avec signature (`STRIPE_WEBHOOK_SECRET`)
- [ ] Dependances a jour (pas de CVE connues)

## Fichiers critiques a auditer
- `mvp/backend/app/auth.py` - Authentification JWT
- `mvp/backend/app/config.py` - Configuration et secrets
- `mvp/backend/app/modules/billing/` - Integration Stripe
- `mvp/backend/app/modules/api_keys/` - Gestion des cles API
- `mvp/backend/app/rate_limit.py` - Rate limiting

## Format du rapport
```
## Rapport de Securite - [date]

### Critique (action immediate)
- [description + fichier:ligne + recommandation]

### Haute (a corriger rapidement)
- [description + fichier:ligne + recommandation]

### Moyenne (a planifier)
- [description + fichier:ligne + recommandation]

### Basse (ameliorations)
- [description + fichier:ligne + recommandation]
```

## Commandes de scan
```bash
cd mvp/backend && pip audit          # Vulnerabilites Python
cd mvp/frontend && npm audit         # Vulnerabilites Node
ruff check app/ --select S           # Regles de securite Ruff (bandit)
```
