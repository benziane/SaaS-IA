---
name: code-review
description: |
  Skill pour la revue de code du projet SaaS-IA.
  TRIGGER quand: l'utilisateur demande une "review", "revue de code",
  ou avant un commit/PR important. Ce skill opere en mode READ-ONLY.
---

# Revue de Code - SaaS-IA

## Mode: READ-ONLY
Ce skill analyse le code sans le modifier. Il produit un rapport avec des recommandations actionnables.

## Checklist de revue

### 1. Architecture
- [ ] Le code respecte l'architecture modulaire (modules avec manifest.json)
- [ ] Separation routes → service → database respectee
- [ ] Pas de logique metier dans les routes
- [ ] Pas d'import circulaire entre modules

### 2. Conventions
- [ ] Nommage Python: snake_case (fonctions, variables), PascalCase (classes)
- [ ] Nommage TypeScript: camelCase (fonctions, variables), PascalCase (composants, types)
- [ ] Commits Conventional Commits: `type(scope): description`
- [ ] Pas de `print()` - utiliser `structlog`

### 3. Qualite
- [ ] Pas de code duplique (DRY) - factoriser si > 3 occurrences
- [ ] Fonctions < 50 lignes (decomposer si trop longues)
- [ ] Gestion d'erreurs explicite (HTTPException avec status codes)
- [ ] Pas de `# TODO` sans issue GitHub associee

### 4. Securite
- [ ] Validation Pydantic sur toutes les entrees
- [ ] Auth JWT sur les endpoints proteges
- [ ] Pas de secrets en dur
- [ ] Rate limiting sur les endpoints publics

### 5. Tests
- [ ] Tests present pour le nouveau code
- [ ] Tests couvrent happy path + cas d'erreur
- [ ] Mocks pour les services externes (IA, Stripe)
- [ ] Pas de tests flaky (pas de sleep, pas de dependance reseau)

### 6. Frontend (si applicable)
- [ ] Utilise les composants Sneat/MUI (pas de composants custom inutiles)
- [ ] TypeScript strict (pas de `any`)
- [ ] TanStack Query pour les appels API
- [ ] Accessible (aria-labels)

### 7. Performance
- [ ] Requetes DB avec SELECT specifique (pas de SELECT *)
- [ ] Pagination sur les listes
- [ ] Pas de N+1 queries
- [ ] Async/await correctement utilise

## Format du rapport
```
## Revue de code - [fichiers revus]

### A corriger (bloquant)
- [description + fichier:ligne + suggestion]

### Recommandations (non-bloquant)
- [description + fichier:ligne + suggestion]

### Points positifs
- [ce qui est bien fait]
```

## Principe
Signaler uniquement les vrais problemes. Ne pas sur-ingenierer ni proposer du refactoring inutile. Pragmatisme > perfectionnisme.
