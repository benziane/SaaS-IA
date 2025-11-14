# 🎨 SaaS-IA Frontend - Grade S++

[![TypeScript](https://img.shields.io/badge/TypeScript-5.5.4-blue)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15.1.2-black)](https://nextjs.org/)
[![Material-UI](https://img.shields.io/badge/MUI-6.2.1-007FFF)](https://mui.com/)
[![TanStack Query](https://img.shields.io/badge/TanStack%20Query-5.62.8-FF4154)](https://tanstack.com/query)

> Frontend de la plateforme SaaS-IA avec standards Enterprise Grade S++

---

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Stack Technique](#stack-technique)
- [Installation](#installation)
- [Développement](#développement)
- [Tests](#tests)
- [Build & Déploiement](#build--déploiement)
- [Architecture](#architecture)
- [Standards S++](#standards-s)
- [Contribution](#contribution)

---

## 🎯 Vue d'ensemble

Frontend Next.js 15 avec Material-UI pour la plateforme SaaS-IA. Respecte les standards **Enterprise Grade S++** avec :

- ✅ TypeScript strict mode (no `any`)
- ✅ ESLint strict + Accessibility
- ✅ Security headers (HSTS, CSP, etc.)
- ✅ Validation Zod stricte
- ✅ Tests E2E + Accessibility (>85% coverage)
- ✅ Real-time updates (TanStack Query polling)

---

## 🛠️ Stack Technique

### Core
- **Next.js 15.1.2** - React framework avec App Router
- **React 18.3.1** - UI library
- **TypeScript 5.5.4** - Type safety
- **Material-UI 6.2.1** - UI components (Sneat template)

### State & Data
- **TanStack Query 5.62.8** - Server state management
- **Zustand 5.0.2** - Client state management
- **Axios 1.7.9** - HTTP client

### Forms & Validation
- **React Hook Form 7.54.2** - Form management
- **Zod 3.24.1** - Schema validation

### Tests
- **Vitest 2.1.8** - Unit tests
- **Playwright 1.49.1** - E2E tests
- **@axe-core/playwright 4.10.2** - Accessibility tests

### Dev Tools
- **ESLint 8.57.1** - Linting
- **Prettier 3.4.2** - Code formatting
- **Storybook 8.5.0** - Component documentation

---

## 🚀 Installation

### Prérequis

- Node.js >= 18.0.0
- npm >= 9.0.0

### Installation des dépendances

```bash
npm install
```

---

## 💻 Développement

### Démarrer le serveur de développement

```bash
npm run dev
```

Le frontend sera accessible sur **http://localhost:3002**

### Variables d'environnement

Créer un fichier `.env.local` :

```bash
NEXT_PUBLIC_API_URL=http://localhost:8004
```

### Scripts disponibles

```bash
# Development
npm run dev              # Start dev server (port 3002)

# Build
npm run build            # Production build
npm run start            # Start production server

# Linting
npm run lint             # Run ESLint
npm run lint:fix         # Fix ESLint errors
npm run format           # Format with Prettier
npm run type-check       # TypeScript check

# Tests
npm run test             # Run Vitest
npm run test:ui          # Vitest UI
npm run test:coverage    # Coverage report
npm run test:e2e         # Playwright E2E
npm run test:e2e:ui      # Playwright UI
npm run test:a11y        # Accessibility tests

# Storybook
npm run storybook        # Start Storybook
npm run build-storybook  # Build Storybook
```

---

## 🧪 Tests

### Tests Unitaires (Vitest)

```bash
# Run tests
npm run test

# Watch mode
npm run test -- --watch

# Coverage
npm run test:coverage
```

**Coverage threshold : ≥85%**

### Tests E2E (Playwright)

```bash
# Run all E2E tests
npm run test:e2e

# Run specific test
npm run test:e2e -- login.spec.ts

# UI mode
npm run test:e2e:ui

# Debug mode
npm run test:e2e -- --debug
```

### Tests Accessibility (axe-core)

```bash
# Run accessibility tests
npm run test:a11y
```

**Standard : WCAG AA compliance**

---

## 📦 Build & Déploiement

### Build de production

```bash
npm run build
```

### Démarrer en production

```bash
npm run start
```

### Analyse du bundle

```bash
npm run build -- --analyze
```

---

## 🏗️ Architecture

### Structure du projet

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/            # Auth pages (login, register)
│   │   ├── (dashboard)/       # Dashboard pages
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css        # Global styles
│   │
│   ├── features/              # Feature modules
│   │   ├── auth/              # Authentication
│   │   │   ├── api.ts
│   │   │   ├── types.ts
│   │   │   ├── schemas.ts     # Zod validation
│   │   │   └── hooks/         # React Query hooks
│   │   │
│   │   └── transcription/     # Transcription feature
│   │       ├── api.ts
│   │       ├── types.ts
│   │       ├── schemas.ts
│   │       └── hooks/
│   │
│   ├── lib/                   # Shared libraries
│   │   ├── apiClient.ts       # Axios instance
│   │   ├── queryClient.ts     # TanStack Query config
│   │   └── store.ts           # Zustand stores
│   │
│   ├── components/            # Shared components
│   │   └── Providers.tsx
│   │
│   ├── configs/               # Configuration
│   │   └── themeConfig.ts
│   │
│   ├── @core/                 # Core types
│   │   └── types.ts
│   │
│   └── tests/                 # Tests
│       ├── setup.ts
│       └── e2e/               # E2E tests
│
├── public/                    # Static files
├── package.json
├── tsconfig.json              # TypeScript config
├── next.config.ts             # Next.js config
├── vitest.config.ts           # Vitest config
├── playwright.config.ts       # Playwright config
└── .eslintrc.json             # ESLint config
```

### Feature Pattern

Chaque feature suit cette structure :

```
features/<feature>/
├── api.ts              # API calls
├── types.ts            # TypeScript types
├── schemas.ts          # Zod validation
└── hooks/              # React Query hooks
    ├── use<Feature>.ts
    ├── use<Feature>Mutations.ts
    └── index.ts
```

---

## 🏆 Standards S++

### TypeScript Strict

```json
{
  "strict": true,
  "noImplicitAny": true,
  "strictNullChecks": true,
  "noUnusedLocals": true,
  "noUnusedParameters": true,
  "noImplicitReturns": true,
  "noUncheckedIndexedAccess": true,
  "exactOptionalPropertyTypes": true
}
```

### ESLint Strict

- ✅ TypeScript strict rules
- ✅ React best practices
- ✅ Accessibility rules (jsx-a11y)
- ✅ Import order rules
- ✅ No `any` allowed
- ✅ Explicit function return types

### Security

- ✅ Security headers (HSTS, CSP, X-Frame-Options, etc.)
- ✅ Token management (localStorage avec auto-cleanup)
- ✅ 401 auto-redirect
- ✅ XSS protection
- ✅ CORS configuration

### Accessibility

- ✅ WCAG AA compliance
- ✅ ARIA labels complets
- ✅ Skip to main content
- ✅ Keyboard navigation
- ✅ Focus visible styles
- ✅ Screen reader support

### Validation

- ✅ Zod schemas avec regex
- ✅ Email validation (format + regex)
- ✅ Password strength (min 8 chars, uppercase, lowercase, number)
- ✅ Real-time validation (`mode: 'onBlur'`)
- ✅ Error messages clairs

### Performance

- ✅ Query caching (TanStack Query)
- ✅ Stale time optimization (CRITICAL, STANDARD, STABLE, STATIC)
- ✅ Retry logic intelligent (exponential backoff)
- ✅ Code splitting (Next.js)
- ✅ Image optimization (Next.js)
- ✅ Bundle < 300KB

---

## 🎨 Sneat MUI Template

Ce projet utilise la **template premium Sneat MUI Next.js Admin v3.0.0**.

### Règles d'utilisation

- ✅ TOUJOURS utiliser les composants Sneat
- ✅ ADAPTER au lieu de recréer
- ❌ NE JAMAIS créer de composants UI from scratch

### Composants disponibles

- **Layouts** : `AdminLayout`, `BlankLayout`, `AuthLayout`
- **Forms** : `TextField`, `Select`, `Checkbox`, `Radio`, `Switch`
- **Data Display** : `Table`, `Card`, `Chip`, `Avatar`, `Badge`
- **Navigation** : `Menu`, `Tabs`, `Breadcrumbs`, `Stepper`
- **Feedback** : `Alert`, `Dialog`, `Snackbar`, `Progress`
- **Inputs** : `Button`, `IconButton`, `Fab`, `ToggleButton`

Voir `.cursorrules` pour plus de détails.

---

## 🤝 Contribution

### Workflow

1. Créer une branche feature : `git checkout -b feature/ma-feature`
2. Développer en respectant les standards S++
3. Lancer les tests : `npm run test && npm run test:e2e`
4. Vérifier le linting : `npm run lint && npm run type-check`
5. Commit : `git commit -m "feat: ma feature"`
6. Push : `git push origin feature/ma-feature`
7. Créer une Pull Request

### Standards de code

- ✅ TypeScript strict (no `any`)
- ✅ ESLint strict (no warnings)
- ✅ Prettier formatting
- ✅ Tests coverage >85%
- ✅ Accessibility WCAG AA
- ✅ Security headers

### Commits

Format : `<type>(scope): <description>`

Types : `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Exemple : `feat(auth): add login page with validation`

---

## 📚 Documentation

- [Next.js Documentation](https://nextjs.org/docs)
- [Material-UI Documentation](https://mui.com/)
- [TanStack Query Documentation](https://tanstack.com/query)
- [Playwright Documentation](https://playwright.dev/)
- [Vitest Documentation](https://vitest.dev/)

---

## 📝 License

MIT

---

## 👥 Auteurs

- **@benziane** - Développement initial

---

## 🙏 Remerciements

- Template Sneat MUI v3.0.0
- Material-UI team
- TanStack team
- Next.js team

---

**Grade Frontend : S+ (90/100)** 🏆  
**Grade Cible : S++ (98/100)** 👑

