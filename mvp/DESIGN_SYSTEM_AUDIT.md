# Audit Design System - SaaS-IA Platform

> **Date** : 2026-03-24
> **Statut** : Etude comparative - AUCUNE modification
> **Objectif** : Identifier le meilleur design system pour la refonte de la plateforme

---

## Table des matieres

1. [Etat actuel du frontend](#1-etat-actuel-du-frontend)
2. [Etat du design-hub](#2-etat-du-design-hub)
3. [Comparatif des design systems](#3-comparatif-des-design-systems)
4. [Analyse detaillee par critere](#4-analyse-detaillee-par-critere)
5. [Matrice de decision](#5-matrice-de-decision)
6. [Recommandation finale](#6-recommandation-finale)
7. [Strategie de migration](#7-strategie-de-migration)

---

## 1. Etat actuel du frontend

### Stack technique en place

| Couche | Techno | Version | Role |
|--------|--------|---------|------|
| Framework | Next.js | 15.5.14 | App Router, SSR, Edge |
| UI Library | MUI (Material) | 6.5.0 | Composants principaux |
| Template | Sneat Admin | - | Layout, navigation, theme |
| CSS-in-JS | Emotion | 11.14.0 | Styling MUI |
| Utility CSS | Tailwind | 3.4.19 | Classes utilitaires |
| Icons | MUI Icons + Boxicons + Iconify | Mixte | 3 systemes non unifies |
| Charts | Recharts + MUI X-Charts | 3.8.0 / 8.28.0 | 2 libs redondantes |
| Animation | Framer Motion | 12.38.0 | Transitions, gestures |
| State | TanStack Query + Zustand | 5.95.0 / 5.0.12 | Server + client state |
| Forms | React Hook Form + Zod | 7.72.0 / 3.25.76 | Validation typee |
| Variants | CVA | 0.7.1 | Component variants |
| Toast | Sonner | 1.7.4 | Notifications |

### Problemes identifies

| # | Probleme | Impact | Severite |
|---|----------|--------|----------|
| 1 | **3 systemes d'icones** (MUI + Boxicons CDN + Iconify) | Bundle size, inconsistance visuelle | Haute |
| 2 | **2 libs de charts** (Recharts + MUI X-Charts) | Redondance, 2 APIs differentes | Moyenne |
| 3 | **3 couches de styling** (Emotion + Tailwind + CSS vars) | Complexite, conflits potentiels | Haute |
| 4 | **Template Sneat** couple a MUI | Migration = refaire tout le layout | Haute |
| 5 | **Font Public Sans** only | Pas alignee avec design-hub (Inter) | Basse |
| 6 | **Tailwind config minimale** | Pas de theme tokens structures | Moyenne |
| 7 | **Theme custom Sneat** (colorSchemes.ts + 37 overrides) | Difficult a maintenir, non standard | Haute |
| 8 | **Pas de composants partages** avec design-hub | Zero reutilisation inter-projets | Haute |

### Metriques actuelles

```
Pages dashboard     : 31 pages (26 routes + layouts)
Features modules    : 23 modules (api + types + hooks)
Composants custom   : ~25 (chat, audio, command palette, etc.)
Overrides MUI       : 37 fichiers de styles
Taille src/         : ~1.8 MB
Dependencies UI     : 18 packages (MUI seul = 6 packages)
```

### Points forts a conserver

- **Architecture features/** : Pattern api.ts + types.ts + hooks/ excellent
- **TanStack Query** : Stale times stratifies, invalidation auto, retry
- **CommandPalette** (Ctrl+K) : 30+ commandes, navigation rapide
- **Auth system** : JWT + refresh + interceptors + guards
- **SSE streaming** : Chat temps reel fonctionnel
- **Testing infra** : Vitest + Playwright + axe-core
- **Dark mode** : System detection + toggle + persistence

---

## 2. Etat du design-hub

### Vue d'ensemble

Le design-hub est un **monorepo pnpm** avec 5 packages partages et une app explorer.

```
design-hub/
├── shared/
│   ├── tokens-core/    → 110 tokens primitifs (7 categories)
│   ├── fonts/          → Inter + Geist + JetBrains Mono (variable)
│   ├── utils/          → cn() + CVA
│   ├── icons/          → Lucide React (wrapper versionne)
│   └── configs/        → Tailwind + PostCSS + ESLint + Prettier + TS + Storybook
├── app/                → Explorer Vite (10 pages)
└── catalog/            → Registre de 9 design systems
```

### Tokens disponibles

| Categorie | Tokens | Exemples |
|-----------|--------|----------|
| Colors (neutral) | 15 | white, black, gray-50 a gray-950, status x4 |
| Spacing | 26 | 0 a 16rem (echelle 4px) |
| Typography | 13 | 3 familles (Inter, JetBrains Mono, Geist), 5 tailles, 4 weights |
| Radius | 9 | none a full (0 a 9999px) |
| Shadows | 8 | sm a 2xl + inner |
| Z-Index | 9 | base(0) a tooltip(1700) |
| Transitions | 11 | 4 durations + 7 easings |

### Pipeline de build tokens

```
JSON primitifs → generate.mjs → tokens.css (CSS vars)
                              → tokens.js/mjs (JS/ESM)
                              → tokens.d.ts (TypeScript)
                              → tailwind.preset.js (Tailwind)
```

### Systemes catalogues (9)

| # | Systeme | Stack | Maturite |
|---|---------|-------|----------|
| 1 | TRT Design System | React + TW 3.4 + CVA | Active, 12 themes |
| 2 | Cockpit UI | React + TW 3.4 + Vite | Active, industriel |
| 3 | TRT AI Hub Monorepo | React + TW 3.4 + Turbo | **Le plus mature** (43 themes) |
| 4 | WeLAB Frontend | React + Radix UI + Cytoscape | Active, 18+ primitives |
| 5 | Lab-SaaS Frontend | React + Radix UI + Recharts | Active, pas de DS formel |
| 6 | Materio DS | React 19 + MUI 7.3.5 | Active, extraction |
| 7 | Sifate Voyage | Vite 6 + TW 4 | En dev, premium |
| 8 | Automation Tool | TypeScript + Python | Active, dark only |
| 9 | AI-COOS Frontend | **Next.js 16 + React 19 + TW 4** | Active, stack la plus recente |

### Compatibilite avec SaaS-IA

| Element | design-hub | SaaS-IA actuel | Compatible ? |
|---------|------------|----------------|--------------|
| Fonts | Inter + JetBrains Mono | Public Sans | **Non** → migrer vers Inter |
| Icons | Lucide React | MUI Icons + Boxicons | **Non** → migrer vers Lucide |
| Styling | Tailwind + CSS vars | Emotion + Tailwind | **Partiel** → eliminer Emotion |
| Tokens | JSON → CSS/TW/JS | MUI theme overrides | **Non** → adopter tokens-core |
| Utils | cn() + CVA | clsx + tailwind-merge + CVA | **Oui** → remplacer par @design-hub/utils |
| Configs | ESLint + Prettier + TS | ESLint + Prettier + TS | **Oui** → unifier |

---

## 3. Comparatif des design systems

### Candidats evalues

| # | Design System | Approche | License |
|---|---------------|----------|---------|
| A | **shadcn/ui** | Copy-paste + Radix + Tailwind | MIT |
| B | **MUI (actuel)** | Library + Emotion + JSS | MIT |
| C | **Mantine** | Library + CSS modules + hooks | MIT |
| D | **Ant Design** | Library + CSS-in-JS + tokens | MIT |
| E | **Chakra UI v3** | Library + Panda CSS + Ark UI | MIT |
| F | **Radix Themes** | Library + Radix primitives | MIT |

### Grille comparative

| Critere | shadcn/ui | MUI 6 | Mantine 7 | Ant Design 5 | Chakra v3 | Radix Themes |
|---------|-----------|-------|-----------|---------------|-----------|--------------|
| **Composants** | 50+ (extensibles) | 60+ | 100+ | 80+ | 50+ | 30+ |
| **Styling** | Tailwind CSS | Emotion | CSS modules | CSS-in-JS | Panda CSS | Radix tokens |
| **Bundle size** | 0 KB (copy-paste) | ~150 KB | ~80 KB | ~200 KB | ~100 KB | ~60 KB |
| **Tailwind natif** | **Oui** | Non | Non | Non | Non | Non |
| **Customisation** | **Totale** (code source) | Theme provider | Theme + CSS | Design tokens | Recipes | Token system |
| **Dark mode** | CSS vars natif | Theme context | color-scheme | CSS vars | Color mode | Theme class |
| **Accessibilite** | Radix (excellent) | Bon | Bon | Moyen | Ark UI (bon) | **Excellent** |
| **App Router** | **Natif** | Adapter requis | Natif | Adapter requis | Natif | Natif |
| **React 18** | Oui | Oui | Oui | Oui | Oui | Oui |
| **TypeScript** | **100%** | 100% | 100% | 95% | 100% | 100% |
| **Maintenance** | Communaute active | Meta/Google | 1 mainteneur | Ant Group (China) | Segun Adebayo | WorkOS |
| **Stars GitHub** | 85K+ | 95K+ | 26K+ | 92K+ | 38K+ | 16K+ |
| **Learning curve** | Faible | Haute | Moyenne | Haute | Moyenne | Faible |
| **Migration effort** | Haut (refonte) | Nul (deja la) | Haut | Tres haut | Haut | Moyen |

---

## 4. Analyse detaillee par critere

### 4.1. Compatibilite avec design-hub

| DS | Tokens JSON | Tailwind | cn() + CVA | Lucide | Score |
|----|-------------|----------|------------|--------|-------|
| **shadcn/ui** | **Natif** (CSS vars) | **Natif** | **Natif** | **Natif** | **10/10** |
| MUI | Non (theme JS) | Non | Non | Non | 1/10 |
| Mantine | Partiel | Non | Non | Non | 2/10 |
| Ant Design | Partiel (tokens) | Non | Non | Non | 2/10 |
| Chakra v3 | Partiel | Non | Non | Non | 2/10 |
| Radix Themes | Oui (CSS vars) | Non | Non | Non | 4/10 |

> **Verdict** : shadcn/ui est le SEUL systeme 100% compatible avec design-hub.
> Meme stack : Tailwind + CSS vars + Radix + Lucide + cn() + CVA.

### 4.2. Performance (bundle size)

| DS | JS envoy au client | CSS | Total estime |
|----|-------------------|-----|--------------|
| **shadcn/ui** | **0 KB** (code source, tree-shake natif) | Tailwind purge | **< 30 KB** |
| MUI | ~150 KB (Emotion runtime + composants) | ~50 KB | ~200 KB |
| Mantine | ~80 KB | ~30 KB CSS modules | ~110 KB |
| Ant Design | ~200 KB | ~100 KB | ~300 KB |
| Chakra v3 | ~100 KB | ~40 KB | ~140 KB |
| Radix Themes | ~60 KB | ~20 KB | ~80 KB |

> **Verdict** : shadcn/ui = performance imbattable. Zero runtime, zero overhead.

### 4.3. Composants specifiques SaaS IA

| Composant necessaire | shadcn/ui | MUI | Mantine | Ant | Chakra | Radix |
|---------------------|-----------|-----|---------|-----|--------|-------|
| Data Table (sort/filter/paginate) | **Oui** (TanStack Table) | Oui (DataGrid) | Oui | Oui | Non | Non |
| Command Palette (Ctrl+K) | **Oui** (cmdk natif) | Non | Spotlight | Non | Non | Non |
| Sheet/Drawer | **Oui** | Oui | Oui | Oui | Oui | Non |
| Tabs | **Oui** | Oui | Oui | Oui | Oui | Oui |
| Dialog/Modal | **Oui** | Oui | Oui | Oui | Oui | Oui |
| Toast | **Oui** (Sonner) | Snackbar | Notifications | Message | Toast | Toast |
| Skeleton loader | **Oui** | Oui | Oui | Oui | Oui | Non |
| Accordion | **Oui** | Oui | Oui | Collapse | Oui | Oui |
| Sidebar navigation | **Oui** (nouveau) | Drawer | NavLink | Menu | Non | Non |
| Charts | Via Recharts | X-Charts | Non | AntV | Non | Non |
| Code block | **Oui** | Non | Code | Non | Non | Non |
| File upload | **Oui** | Non | Dropzone | Upload | Non | Non |
| Date picker | **Oui** | Oui | Oui | Oui | Non | Non |
| Badge/Chip | **Oui** | Chip | Badge | Tag | Badge | Badge |
| Progress | **Oui** | Oui | Oui | Oui | Oui | Oui |
| Tooltip | **Oui** | Oui | Oui | Oui | Oui | Oui |
| Avatar | **Oui** | Oui | Oui | Oui | Oui | Oui |
| Breadcrumb | **Oui** | Oui | Oui | Oui | Oui | Non |

> **Verdict** : shadcn/ui couvre 100% de nos besoins avec des composants de haute qualite.

### 4.4. Ecosysteme et extensions

| DS | Admin templates | AI components | Visual builders | Formulaires avances |
|----|----------------|---------------|-----------------|---------------------|
| **shadcn/ui** | **10+** (taxonomy, shadcn-admin, next-shadcn-dashboard) | **chat-ui, ai-chatbot** | React Flow compatible | react-hook-form natif |
| MUI | 5+ (Sneat, Berry, Materio) | Peu | Non | MUI X (payant) |
| Mantine | 3+ | Peu | Non | Mantine Form |
| Ant Design | 5+ (Ant Design Pro) | Peu | AntV G6 | ProForm |
| Chakra | 2+ | Peu | Non | Non |
| Radix | 1+ | Peu | Non | Non |

> **Verdict** : shadcn/ui a l'ecosysteme IA le plus riche en 2026.

### 4.5. Migration depuis MUI

| Vers | Effort | Coexistence possible | Risque | Duree estimee |
|------|--------|---------------------|--------|---------------|
| **shadcn/ui** | Moyen-haut (31 pages) | **Oui** (Tailwind deja la) | Faible | 3-4 semaines |
| Mantine | Tres haut | Non (conflit CSS) | Moyen | 5-6 semaines |
| Ant Design | Tres haut | Non (conflit CSS) | Haut | 6-8 semaines |
| Chakra v3 | Haut | Non (Panda CSS) | Moyen | 5-6 semaines |
| Radix Themes | Moyen | Oui (CSS vars) | Faible | 3-4 semaines |

> **Verdict** : shadcn/ui et Radix Themes permettent une migration progressive avec coexistence MUI.

---

## 5. Matrice de decision

### Scoring (1-10, poids x critere)

| Critere | Poids | shadcn/ui | MUI 6 | Mantine 7 | Ant 5 | Chakra v3 | Radix |
|---------|-------|-----------|-------|-----------|-------|-----------|-------|
| Compat design-hub | x3 | **10** | 1 | 2 | 2 | 2 | 4 |
| Performance | x2 | **10** | 5 | 7 | 4 | 6 | 8 |
| Composants SaaS IA | x2 | **9** | 8 | 7 | 8 | 5 | 5 |
| Ecosysteme 2026 | x2 | **10** | 7 | 5 | 6 | 5 | 4 |
| Customisation | x2 | **10** | 6 | 7 | 5 | 7 | 8 |
| Accessibilite | x1 | **9** | 7 | 7 | 5 | 8 | 10 |
| Migration effort | x1 | 6 | **10** | 3 | 2 | 3 | 6 |
| Maintenance long terme | x1 | 8 | **9** | 5 | 7 | 6 | 8 |
| **TOTAL PONDERE** | **/140** | **130** | 82 | 72 | 66 | 66 | 82 |

### Classement final

```
1er  shadcn/ui      130/140  ██████████████████████████████  93%
2eme MUI 6           82/140  ██████████████████░░░░░░░░░░░░  59%
2eme Radix Themes    82/140  ██████████████████░░░░░░░░░░░░  59%
4eme Mantine 7       72/140  ████████████████░░░░░░░░░░░░░░  51%
5eme Ant Design 5    66/140  ██████████████░░░░░░░░░░░░░░░░  47%
5eme Chakra v3       66/140  ██████████████░░░░░░░░░░░░░░░░  47%
```

---

## 6. Recommandation finale

### **WINNER : shadcn/ui** (Score 93%)

#### Pourquoi shadcn/ui est le choix evident pour SaaS-IA

**1. Alignement parfait avec design-hub**
- Meme stack exacte : Tailwind + CSS vars + Radix + Lucide + cn() + CVA
- Les tokens de design-hub s'injectent directement via `tailwind.preset.js`
- Zero adaptateur, zero wrapper, zero friction

**2. Zero runtime, performance maximale**
- Pas de library JS envoyee au client (copy-paste dans le projet)
- Tree-shaking naturel : on n'importe que ce qu'on utilise
- Tailwind purge = CSS minimal en production

**3. Customisation totale**
- Le code source est DANS le projet, pas dans node_modules
- On peut modifier chaque composant sans fork ni override hacky
- Les CSS variables permettent le theming dynamique

**4. Ecosysteme IA riche en 2026**
- `shadcn-chat` : composants chat avec streaming
- `shadcn-admin` : templates dashboard complets
- `cmdk` : command palette native
- React Flow : s'integre naturellement avec Tailwind
- Sonner : deja dans notre stack

**5. Migration progressive possible**
- MUI et shadcn peuvent coexister (pas de conflit CSS)
- On migre page par page, module par module
- Tailwind est deja dans notre stack (base existante)

#### Stack cible apres migration

```
UI Components   : shadcn/ui (50+ composants, copy-paste)
Primitives      : Radix UI (accessibilite, headless)
Styling         : Tailwind CSS (design-hub/tokens-core preset)
Tokens          : @design-hub/tokens-core (JSON → CSS → TW)
Fonts           : @design-hub/fonts (Inter + JetBrains Mono)
Icons           : @design-hub/icons (Lucide React)
Utils           : @design-hub/utils (cn + CVA)
Configs         : @design-hub/configs (TW + ESLint + Prettier + TS)
Animation       : Framer Motion (conserver)
Charts          : Recharts (conserver, unifier)
Forms           : React Hook Form + Zod (conserver)
State           : TanStack Query + Zustand (conserver)
Toast           : Sonner (conserver, deja shadcn-compatible)
Command palette : cmdk (remplacer custom par shadcn)
```

#### Ce qu'on SUPPRIME

| Supprime | Remplace par |
|----------|-------------|
| @mui/material (6 packages) | shadcn/ui composants |
| @emotion/* (3 packages) | Tailwind CSS |
| @mui/icons-material | @design-hub/icons (Lucide) |
| @mui/x-charts | Recharts (unifier) |
| Boxicons CDN | @design-hub/icons (Lucide) |
| Iconify | @design-hub/icons (Lucide) |
| Sneat template (@core/, @menu/, @layouts/) | shadcn sidebar + layout |
| Public Sans font | @design-hub/fonts (Inter) |
| 37 fichiers d'overrides MUI | CSS vars + Tailwind |

**Reduction estimee** : -18 packages, -500 KB bundle, -37 fichiers de config theme

#### Ce qu'on CONSERVE

| Conserve | Raison |
|----------|--------|
| Framer Motion | Animations complexes, shadcn-compatible |
| Recharts | Charts fonctionnels, compatible Tailwind |
| React Hook Form + Zod | Formulaires typees, shadcn-natif |
| TanStack Query + Zustand | State management optimal |
| Sonner | Toast deja shadcn-compatible |
| CVA | Deja dans design-hub/utils |
| Architecture features/ | Pattern excellent, ne pas toucher |
| AuthContext + Guards | Auth fonctionnel |
| API client + interceptors | Backend integration solide |
| Playwright + Vitest | Testing infra |

---

## 7. Strategie de migration

### Principes

1. **Progressive** : page par page, jamais big-bang
2. **Coexistence** : MUI et shadcn coexistent pendant la transition
3. **Feature-first** : migrer les features les plus utilisees en premier
4. **Zero regression** : chaque page migree doit etre fonctionnellement identique

### Phases proposees

#### Phase 0 : Foundation (2-3 jours)

```
[ ] Installer shadcn/ui (npx shadcn@latest init)
[ ] Configurer tailwind.config avec @design-hub/tokens-core preset
[ ] Importer @design-hub/fonts (Inter + JetBrains Mono)
[ ] Importer @design-hub/icons (Lucide)
[ ] Importer @design-hub/utils (cn + CVA)
[ ] Creer le nouveau layout shadcn (sidebar + header)
[ ] Configurer les CSS variables shadcn (avec nos tokens)
[ ] Creer le mapping de couleurs : MUI palette → CSS vars
```

#### Phase 1 : Core Layout (3-4 jours)

```
[ ] Migrer Sidebar (Sneat VerticalNav → shadcn Sidebar)
[ ] Migrer Header/Navbar (Sneat → shadcn custom)
[ ] Migrer CommandPalette (custom → shadcn cmdk)
[ ] Migrer Providers wrapper
[ ] Migrer AuthGuard / GuestGuard
[ ] Migrer Dark mode toggle (MUI → shadcn)
[ ] Tester navigation complete
```

#### Phase 2 : Pages prioritaires (5-7 jours)

```
[ ] Dashboard principal (KPI cards, charts)
[ ] Chat (streaming, messages, sidebar)
[ ] Knowledge (upload, search, RAG)
[ ] Transcription (YouTube, audio, results)
[ ] Agents (input, execution, history)
```

#### Phase 3 : Pages secondaires (5-7 jours)

```
[ ] Compare (multi-model, voting)
[ ] Pipelines (visual builder avec React Flow)
[ ] Content Studio (multi-format generation)
[ ] Workflows (DAG editor)
[ ] Crews (multi-agent teams)
```

#### Phase 4 : Pages restantes (3-5 jours)

```
[ ] Data Analyst (upload, charts, insights)
[ ] Images / Video / Voice
[ ] Fine-tuning (datasets, training)
[ ] Security / Monitoring / Memory / Search
[ ] Billing / Profile / API Keys / Costs
```

#### Phase 5 : Cleanup (2-3 jours)

```
[ ] Supprimer toutes les dependances MUI
[ ] Supprimer @emotion/*
[ ] Supprimer Sneat template (@core/, @menu/, @layouts/)
[ ] Supprimer Boxicons CDN
[ ] Supprimer Iconify
[ ] Audit bundle size final
[ ] Tests E2E complets
[ ] Audit accessibilite (axe-core)
```

### Timeline estimee

```
Phase 0 : Foundation        [J1 ─── J3]
Phase 1 : Core Layout       [J3 ────── J7]
Phase 2 : Pages prio        [J7 ─────────── J14]
Phase 3 : Pages sec         [J14 ────────── J21]
Phase 4 : Pages restantes   [J21 ──────── J26]
Phase 5 : Cleanup           [J26 ─── J28]
                            ─────────────────────
                            Total : ~4 semaines
```

---

## Annexe A : Repos de reference shadcn/ui pour SaaS IA

### Templates admin

| Repo | Stars | Pertinence |
|------|-------|------------|
| shadcn-admin | 5K+ | Dashboard admin complet, sidebar, dark mode |
| taxonomy | 18K+ | Blog/content platform Next.js + shadcn |
| next-shadcn-dashboard-starter | 2K+ | Starter dashboard avec charts |
| shadcn-landing-page | 3K+ | Landing page components |

### Composants IA specifiques

| Repo | Stars | Pertinence |
|------|-------|------------|
| chatbot-ui | 28K+ | Chat interface complete (streaming, markdown) |
| assistant-ui | 2K+ | AI assistant components (shadcn natif) |
| vercel/ai-chatbot | 8K+ | Reference officielle Vercel AI SDK + shadcn |
| shadcn-chat | 1K+ | Chat components pour shadcn |

### Visual builders

| Repo | Stars | Pertinence |
|------|-------|------------|
| reactflow | 25K+ | Pipeline/DAG builder (compatible Tailwind) |
| xyflow | 35K+ | Nouvelle version de React Flow |

---

## Annexe B : Mapping composants MUI → shadcn

| MUI | shadcn/ui | Notes |
|-----|-----------|-------|
| `<Button>` | `<Button>` | Variants: default, destructive, outline, secondary, ghost, link |
| `<TextField>` | `<Input>` | Plus simple, CSS vars |
| `<Select>` | `<Select>` | Radix-based, accessible |
| `<Dialog>` | `<Dialog>` | Radix-based |
| `<Drawer>` | `<Sheet>` | Side panel |
| `<Card>` | `<Card>` | CardHeader, CardContent, CardFooter |
| `<Chip>` | `<Badge>` | Inline labels |
| `<Tabs>` | `<Tabs>` | Radix-based |
| `<Accordion>` | `<Accordion>` | Radix-based |
| `<Tooltip>` | `<Tooltip>` | Radix-based |
| `<CircularProgress>` | `<Spinner>` | Custom ou Lucide Loader |
| `<LinearProgress>` | `<Progress>` | Native HTML progress |
| `<Snackbar>` | Sonner `toast()` | Deja en place |
| `<Menu>` | `<DropdownMenu>` | Radix-based |
| `<Grid>` | Tailwind grid/flex | Utility classes |
| `<Stack>` | Tailwind flex | `flex flex-col gap-*` |
| `<Box>` | `<div>` + Tailwind | Plus de Box |
| `<Typography>` | HTML tags + Tailwind | `<h1 className="text-2xl font-bold">` |
| `<List>` | HTML `<ul>` + Tailwind | Semantic HTML |
| `<Avatar>` | `<Avatar>` | Radix-based |
| `<Switch>` | `<Switch>` | Radix-based |
| `<Checkbox>` | `<Checkbox>` | Radix-based |
| `<Slider>` | `<Slider>` | Radix-based |
| `<DataGrid>` | `<DataTable>` | TanStack Table + shadcn |
| `<DatePicker>` | `<DatePicker>` | react-day-picker |
| `<Alert>` | `<Alert>` | Variants: default, destructive |
| `<Breadcrumbs>` | `<Breadcrumb>` | Composable |
| `<Divider>` | `<Separator>` | Radix-based |
| `<Skeleton>` | `<Skeleton>` | Animated placeholder |

---

## Annexe C : Design-hub integration checklist

```
[ ] npm install @design-hub/tokens-core @design-hub/fonts @design-hub/utils @design-hub/icons @design-hub/configs
[ ] tailwind.config.ts : ajouter tokens-core preset + configs base-preset
[ ] globals.css : @import '@design-hub/fonts/css' + @import '@design-hub/tokens-core/css'
[ ] Remplacer imports MUI Icons → import { X } from '@design-hub/icons'
[ ] Remplacer clsx/tailwind-merge → import { cn } from '@design-hub/utils'
[ ] Remplacer Public Sans → Inter (via @design-hub/fonts)
[ ] Mapper CSS vars shadcn sur design-hub tokens
```

---

> **Conclusion** : shadcn/ui est le choix unanime pour SaaS-IA. Alignement parfait avec design-hub, performance superieure, ecosysteme IA riche, migration progressive possible. Le ROI est maximal avec un effort raisonnable (~4 semaines pour 31 pages).
