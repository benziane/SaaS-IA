# Guide de Contribution

Merci de votre intérêt pour contribuer à **SaaS-IA** ! 🎉

## 📋 Table des matières

- [Code de Conduite](#code-de-conduite)
- [Comment contribuer](#comment-contribuer)
- [Processus de développement](#processus-de-développement)
- [Standards de code](#standards-de-code)
- [Commits et Pull Requests](#commits-et-pull-requests)
- [Tests](#tests)
- [Documentation](#documentation)

## 📜 Code de Conduite

En participant à ce projet, vous acceptez de respecter notre code de conduite. Soyez respectueux et constructif dans toutes vos interactions.

## 🤝 Comment contribuer

### Signaler un bug

1. Vérifiez que le bug n'a pas déjà été signalé dans les [Issues](https://github.com/benziane/SaaS-IA/issues)
2. Créez une nouvelle issue en utilisant le template "Bug Report"
3. Fournissez autant de détails que possible

### Proposer une fonctionnalité

1. Vérifiez que la fonctionnalité n'a pas déjà été proposée
2. Créez une nouvelle issue en utilisant le template "Feature Request"
3. Expliquez clairement la motivation et les bénéfices

### Soumettre une Pull Request

1. Fork le repository
2. Créez une branche depuis `develop` : `git checkout -b feature/ma-fonctionnalite`
3. Faites vos modifications
4. Commitez vos changements (voir [Conventions de commit](#conventions-de-commit))
5. Pushez vers votre fork : `git push origin feature/ma-fonctionnalite`
6. Ouvrez une Pull Request vers `develop`

## 🔄 Processus de développement

### Structure des branches

- `main` : Code en production, stable
- `develop` : Branche de développement principale
- `feature/*` : Nouvelles fonctionnalités
- `fix/*` : Corrections de bugs
- `hotfix/*` : Corrections urgentes pour la production

### Workflow Git

```bash
# 1. Cloner le repository
git clone https://github.com/benziane/SaaS-IA.git
cd SaaS-IA

# 2. Créer une branche depuis develop
git checkout develop
git pull origin develop
git checkout -b feature/ma-fonctionnalite

# 3. Faire vos modifications
# ... codez ...

# 4. Commiter vos changements
git add .
git commit -m "feat: ajouter ma fonctionnalité"

# 5. Pousser vers votre fork
git push origin feature/ma-fonctionnalite

# 6. Créer une Pull Request sur GitHub
```

## 💻 Standards de code

### Backend (Python)

- **Style** : PEP 8
- **Formatter** : Black
- **Linter** : Ruff
- **Type checking** : MyPy
- **Docstrings** : Google style

```bash
# Formater le code
black backend/app

# Linter
ruff check backend/app

# Type checking
mypy backend/app
```

### Frontend (TypeScript/React)

- **Style** : ESLint + Prettier
- **Conventions** : Airbnb style guide
- **Components** : Functional components + Hooks

```bash
# Linter
npm run lint

# Formater
npm run format

# Type checking
npm run type-check
```

### Conventions de nommage

**Backend (Python):**
- Classes : `PascalCase`
- Fonctions/méthodes : `snake_case`
- Variables : `snake_case`
- Constantes : `UPPER_SNAKE_CASE`

**Frontend (TypeScript):**
- Components : `PascalCase`
- Hooks : `camelCase` (préfixe `use`)
- Fonctions : `camelCase`
- Variables : `camelCase`
- Constantes : `UPPER_SNAKE_CASE`

## 📝 Commits et Pull Requests

### Conventions de commit

Nous suivons la convention [Conventional Commits](https://www.conventionalcommits.org/).

Format : `<type>(<scope>): <description>`

**Types:**
- `feat` : Nouvelle fonctionnalité
- `fix` : Correction de bug
- `docs` : Documentation
- `style` : Formatage (pas de changement de code)
- `refactor` : Refactoring
- `test` : Ajout/modification de tests
- `chore` : Tâches de maintenance
- `perf` : Amélioration de performance
- `ci` : CI/CD

**Exemples:**
```bash
feat(transcription): add multi-language support
fix(api): resolve authentication timeout issue
docs(readme): update installation instructions
test(backend): add unit tests for transcription service
```

### Pull Request Checklist

Avant de soumettre une PR, assurez-vous que :

- [ ] Le code suit les standards du projet
- [ ] Les tests passent (`pytest` pour backend, `npm test` pour frontend)
- [ ] La couverture de tests est maintenue (≥ 80%)
- [ ] La documentation est à jour
- [ ] Les commits suivent les conventions
- [ ] Le code est formaté correctement
- [ ] Pas de conflits avec `develop`

## 🧪 Tests

### Backend

```bash
cd v0/backend

# Lancer tous les tests
pytest

# Avec couverture
pytest --cov=app --cov-report=html

# Tests spécifiques
pytest tests/test_transcription.py -v
```

### Frontend

```bash
cd v0/frontend

# Lancer tous les tests
npm test

# Avec couverture
npm test -- --coverage

# Mode watch
npm test -- --watch
```

### Tests requis

- **Tests unitaires** : Pour toute nouvelle fonction/méthode
- **Tests d'intégration** : Pour les endpoints API
- **Tests E2E** : Pour les flux utilisateur critiques

## 📚 Documentation

### Code

- Commentez le code complexe
- Utilisez des docstrings pour les fonctions/classes
- Ajoutez des exemples d'utilisation

### Documentation projet

- Mettez à jour le README si nécessaire
- Documentez les nouvelles APIs dans `docs/API.md`
- Ajoutez des guides dans `docs/` si pertinent

## 🎯 Bonnes pratiques

### Backend

- ✅ Utilisez `async/await` pour les opérations I/O
- ✅ Validez les entrées avec Pydantic
- ✅ Gérez les erreurs de manière appropriée
- ✅ Loggez les événements importants
- ✅ Écrivez des tests pour chaque service

### Frontend

- ✅ Utilisez TypeScript strict
- ✅ Composants fonctionnels + Hooks
- ✅ Gérez l'état avec React Query
- ✅ Accessibilité (ARIA labels)
- ✅ Responsive design

### Sécurité

- ❌ Jamais de secrets dans le code
- ✅ Utilisez `.env` pour la configuration
- ✅ Validez toutes les entrées utilisateur
- ✅ Sanitizez les données
- ✅ Suivez les principes OWASP

## 🆘 Besoin d'aide ?

- 📖 Consultez la [documentation](./v0/docs/)
- 💬 Ouvrez une [Discussion](https://github.com/benziane/SaaS-IA/discussions)
- 🐛 Signalez un [Bug](https://github.com/benziane/SaaS-IA/issues/new?template=bug_report.md)
- ✨ Proposez une [Fonctionnalité](https://github.com/benziane/SaaS-IA/issues/new?template=feature_request.md)

## 📄 Licence

En contribuant à ce projet, vous acceptez que vos contributions soient sous la même [licence MIT](./v0/LICENSE) que le projet.

---

**Merci de contribuer à SaaS-IA ! 🚀**

