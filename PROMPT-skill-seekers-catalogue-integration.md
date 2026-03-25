# Prompt : Intégrer le Catalogue Claude Skills dans le module Skill Seekers

## Contexte

Le module `skill_seekers` est **déjà 100% implémenté** dans SaaS-IA MVP. Cette tâche consiste uniquement à enrichir la page existante avec un **catalogue interactif de repos suggérés**, issu du rapport `claude-skills-report.html` disponible dans `C:\Users\ibzpc\Git\Idées\Claude_Skills\claude-skills-report.html`.

L'objectif : permettre à l'utilisateur de choisir des repos à scraper depuis un catalogue visuel cliquable, au lieu de saisir les noms manuellement.

---

## Ce qui existe déjà (NE PAS MODIFIER)

### Backend — complet, ne toucher à rien
```
mvp/backend/app/modules/skill_seekers/
  manifest.json    ✅
  __init__.py      ✅
  schemas.py       ✅  (ScrapeJobCreate, ScrapeJobRead, PaginatedJobs, ScrapeJobStats)
  service.py       ✅  (SkillSeekersService, mock mode, CLI detect)
  routes.py        ✅  (POST/GET/DELETE /api/skill-seekers/jobs, /status, /download)
  tasks.py         ✅  (Celery + BackgroundTasks)
mvp/backend/app/models/skill_seekers.py  ✅  (ScrapeJob, ScrapeJobStatus)
mvp/backend/alembic/versions/20260325_0008_skill_seekers.py  ✅
```

### Frontend — existant, enrichir uniquement
```
mvp/frontend/src/features/skill-seekers/
  types.ts         ✅  (ScrapeJob, ScrapeJobStatus, ScrapeJobCreateRequest, etc.)
  api.ts           ✅  (createScrapeJob, getScrapeJobs, etc.)
  hooks/
    useSkillSeekers.ts           ✅
    useSkillSeekersMutations.ts  ✅  (useCreateScrapeJob, useDeleteScrapeJob, useRetryScrapeJob, useCancelScrapeJob)

mvp/frontend/src/app/(dashboard)/skill-seekers/page.tsx  ✅  (18KB — page complète)
```

### Formulaire existant dans page.tsx
Le formulaire actuel utilise :
```typescript
const [repoInput, setRepoInput] = useState('');
const [repos, setRepos] = useState<string[]>([]);
const [targets, setTargets] = useState<string[]>(['claude']);
const [enhance, setEnhance] = useState(false);
```
Le bouton "Add repo" valide le pattern `^[a-zA-Z0-9_\-\.]+\/[a-zA-Z0-9_\-\.]+$`.

---

## Ce qu'il faut créer

### 1 seul nouveau fichier

```
mvp/frontend/src/features/skill-seekers/catalogue.ts
```

### 1 modification de fichier existant

```
mvp/frontend/src/app/(dashboard)/skill-seekers/page.tsx
```

---

## Fichier 1 — `catalogue.ts`

Créer le fichier `mvp/frontend/src/features/skill-seekers/catalogue.ts` avec les données du rapport interactif :

```typescript
/**
 * Claude Skills Catalogue
 * Source : claude-skills-report.html (C:\Users\ibzpc\Git\Idées\Claude_Skills\)
 * Repos suggérés pour le scraping Skill Seekers
 */

export type CatalogueCategory = 'official' | 'community' | 'framework' | 'skill' | 'tool' | 'resource';

export interface CatalogueRepo {
  repo: string;           // format owner/repo
  name: string;           // nom affiché
  description: string;    // description courte
  category: CatalogueCategory;
  stars: number;
  score: number;          // score pertinence 1-10
  tags: string[];
  ghUrl: string;
}

export const CATALOGUE_REPOS: CatalogueRepo[] = [
  {
    repo: 'anthropics/claude-code',
    name: 'Claude Code',
    description: 'CLI officiel de coding agentic d\'Anthropic',
    category: 'official',
    stars: 82500,
    score: 10,
    tags: ['Terminal', 'Agentic', 'TypeScript'],
    ghUrl: 'https://github.com/anthropics/claude-code',
  },
  {
    repo: 'anthropics/claude-cookbooks',
    name: 'Claude Cookbooks',
    description: 'Notebooks Jupyter et recettes pratiques pour l\'API Claude',
    category: 'official',
    stars: 36100,
    score: 8,
    tags: ['Jupyter', 'RAG', 'Python'],
    ghUrl: 'https://github.com/anthropics/claude-cookbooks',
  },
  {
    repo: 'anthropics/claude-agent-sdk',
    name: 'Claude Agent SDK',
    description: 'SDK TypeScript officiel pour agents IA autonomes',
    category: 'official',
    stars: 1000,
    score: 9,
    tags: ['TypeScript', 'SDK', 'Agents'],
    ghUrl: 'https://github.com/anthropics/claude-agent-sdk',
  },
  {
    repo: 'travisvn/awesome-claude-skills',
    name: 'Awesome Claude Skills',
    description: 'Répertoire curé de skills Claude pour tâches spécialisées',
    category: 'community',
    stars: 9700,
    score: 8,
    tags: ['Skills', 'Curated', 'YAML'],
    ghUrl: 'https://github.com/travisvn/awesome-claude-skills',
  },
  {
    repo: 'hesreallyhim/awesome-claude-code',
    name: 'Awesome Claude Code',
    description: 'Répertoire d\'agents, hooks, plugins et outils Claude Code',
    category: 'community',
    stars: 3000,
    score: 7,
    tags: ['Hooks', 'CLAUDE.md', 'Slash-commands'],
    ghUrl: 'https://github.com/hesreallyhim/awesome-claude-code',
  },
  {
    repo: 'obra/superpowers',
    name: 'Superpowers',
    description: 'Framework agentic avec méthodologie TDD et specs atomiques',
    category: 'framework',
    stars: 112000,
    score: 9,
    tags: ['TDD', 'Shell', 'Multi-agent'],
    ghUrl: 'https://github.com/obra/superpowers',
  },
  {
    repo: 'asklokesh/loki-mode',
    name: 'Loki Mode',
    description: 'Système multi-agent autonome : PRD → produit déployé',
    category: 'framework',
    stars: 5000,
    score: 9,
    tags: ['41 agents', '8 swarms', 'RARV'],
    ghUrl: 'https://github.com/asklokesh/loki-mode',
  },
  {
    repo: 'gsd-build/get-shit-done',
    name: 'Get Shit Done',
    description: 'Système spec-driven résolvant la dégradation de contexte',
    category: 'framework',
    stars: 2000,
    score: 8,
    tags: ['Spec-driven', 'XML', 'Parallel waves'],
    ghUrl: 'https://github.com/gsd-build/get-shit-done',
  },
  {
    repo: 'nextlevelbuilder/ui-ux-pro-max-skill',
    name: 'UI/UX Pro Max',
    description: 'Intelligence design IA — 161 règles, 67+ styles, 161 palettes',
    category: 'skill',
    stars: 50200,
    score: 9,
    tags: ['Design System', 'React', 'Flutter'],
    ghUrl: 'https://github.com/nextlevelbuilder/ui-ux-pro-max-skill',
  },
  {
    repo: 'asklokesh/claudeskill-loki-mode',
    name: 'Loki Mode Skill',
    description: 'Version Skill : 37 agents, PRD → revenue, zéro intervention',
    category: 'skill',
    stars: 1200,
    score: 8,
    tags: ['37 agents', 'SKILL.md', 'PRD→Revenue'],
    ghUrl: 'https://github.com/asklokesh/claudeskill-loki-mode',
  },
  {
    repo: 'yusufkaraaslan/Skill_Seekers',
    name: 'Skill Seekers',
    description: 'Preprocessing 17 sources → 16 formats IA dont Claude Skills',
    category: 'tool',
    stars: 11200,
    score: 8,
    tags: ['17 sources', 'RAG', 'OCR', 'AST'],
    ghUrl: 'https://github.com/yusufkaraaslan/Skill_Seekers',
  },
  {
    repo: 'public-apis/public-apis',
    name: 'Public APIs',
    description: 'Plus grande collection d\'APIs publiques gratuites (416k ⭐)',
    category: 'resource',
    stars: 416000,
    score: 7,
    tags: ['50+ catégories', 'HTTPS', 'CORS'],
    ghUrl: 'https://github.com/public-apis/public-apis',
  },
];

export const CATEGORY_LABELS: Record<CatalogueCategory, string> = {
  official: 'Officiel',
  community: 'Community',
  framework: 'Framework',
  skill: 'Skill',
  tool: 'Outil',
  resource: 'Ressource',
};

export const CATEGORY_COLORS: Record<CatalogueCategory, string> = {
  official: '#3b82f6',
  community: '#10b981',
  framework: '#8b5cf6',
  skill: '#f59e0b',
  tool: '#ec4899',
  resource: '#06b6d4',
};

export const ALL_CATEGORIES = Object.keys(CATEGORY_LABELS) as CatalogueCategory[];
```

---

## Fichier 2 — Modification de `page.tsx`

Lire d'abord l'intégralité de `page.tsx` pour comprendre sa structure exacte, puis ajouter le catalogue **sans rien casser**.

### Ce qu'il faut ajouter dans page.tsx

#### A. Import en tête de fichier
```typescript
import {
  CATALOGUE_REPOS,
  CATEGORY_LABELS,
  CATEGORY_COLORS,
  ALL_CATEGORIES,
  type CatalogueCategory,
} from '@/features/skill-seekers/catalogue';
```

#### B. State supplémentaire (dans le composant, après les états existants)
```typescript
const [catalogueOpen, setCatalogueOpen] = useState(false);
const [catalogueFilter, setCatalogueFilter] = useState<CatalogueCategory | 'all'>('all');
```

#### C. Composant `SkillCatalogueDrawer` (à définir dans le même fichier)

Créer un composant local (avant le `export default`) :

```typescript
function SkillCatalogueDrawer({
  open,
  onClose,
  selectedRepos,
  onToggle,
  filter,
  onFilterChange,
}: {
  open: boolean;
  onClose: () => void;
  selectedRepos: string[];
  onToggle: (repo: string) => void;
  filter: CatalogueCategory | 'all';
  onFilterChange: (f: CatalogueCategory | 'all') => void;
}) { ... }
```

Le Drawer affiche :
- **Header** : titre "Catalogue Claude Skills" + bouton fermer
- **Filtres** : chips horizontaux "Tous | Officiel | Community | Framework | Skill | Outil | Ressource"
- **Grille de cartes** : une card MUI par repo avec :
  - Badge coloré (catégorie) en haut à droite
  - Nom + repo slug (`owner/repo`)
  - Description courte
  - Tags (Chips xs)
  - Stars formatées (ex : "112k ⭐")
  - Checkbox ou bouton "Ajouter" — grisé si déjà dans `selectedRepos` ou si `selectedRepos.length >= 10`
- **Footer sticky** : "X repos sélectionnés — Ajouter au job [Confirmer]"

Composants MUI à utiliser : `Drawer`, `Box`, `Typography`, `Chip`, `Card`, `CardContent`, `CardActions`, `Checkbox`, `Button`, `IconButton`, `Divider`, `Stack`.

#### D. Bouton catalogue dans le formulaire existant

Dans la section formulaire existante (là où se trouve le `TextField` de saisie repo), ajouter juste à côté du TextField existant un bouton :

```tsx
<Button
  variant="outlined"
  startIcon={<AutoAwesomeIcon />}
  onClick={() => setCatalogueOpen(true)}
  size="small"
>
  Catalogue
</Button>
```

Importer `AutoAwesomeIcon` depuis `@mui/icons-material/AutoAwesome`.

#### E. Rendu du Drawer (en bas du JSX, avant la fermeture du fragment principal)
```tsx
<SkillCatalogueDrawer
  open={catalogueOpen}
  onClose={() => setCatalogueOpen(false)}
  selectedRepos={repos}
  onToggle={(repo) => {
    setRepos((prev) =>
      prev.includes(repo) ? prev.filter((r) => r !== repo) : [...prev, repo]
    );
  }}
  filter={catalogueFilter}
  onFilterChange={setCatalogueFilter}
/>
```

---

## Contraintes impératives

1. **Ne pas modifier** `schemas.py`, `service.py`, `routes.py`, `tasks.py`, `manifest.json`, `types.ts`, `api.ts`, `hooks/`
2. **Ne pas casser** la logique existante de `page.tsx` — ajouter uniquement, ne pas réécrire
3. **Validation conservée** : le pattern regex `^[a-zA-Z0-9_\-\.]+\/[a-zA-Z0-9_\-\.]+$` doit toujours s'appliquer sur les repos du catalogue (ils le respectent tous déjà)
4. **Limite 10 repos** : le bouton "Ajouter" dans le catalogue est désactivé si `repos.length >= 10`
5. **Déduplication** : si un repo du catalogue est déjà dans `repos`, sa card affiche "Déjà ajouté" (checkbox cochée, non cliquable)
6. **Responsive** : grille de cartes en `xs=12 sm=6 md=4` dans le Drawer
7. **TypeScript strict** : pas de `any`, typer correctement avec les interfaces de `catalogue.ts`
8. **Aucune dépendance externe** : utiliser uniquement MUI 6 + React déjà installés

---

## Ordre d'implémentation

```
1. Créer  mvp/frontend/src/features/skill-seekers/catalogue.ts
2. Lire   mvp/frontend/src/app/(dashboard)/skill-seekers/page.tsx en entier
3. Ajouter l'import catalogue dans page.tsx
4. Ajouter les 2 states (catalogueOpen, catalogueFilter)
5. Définir le composant SkillCatalogueDrawer avant export default
6. Ajouter le bouton "Catalogue" dans le formulaire existant
7. Ajouter le <SkillCatalogueDrawer ... /> dans le JSX
```

---

## Vérification

```bash
# TypeScript sans erreur
cd mvp/frontend && pnpm type-check

# Build sans erreur
pnpm build

# Comportement attendu :
# 1. Page /skill-seekers s'ouvre normalement (rien de cassé)
# 2. Bouton "Catalogue" visible dans la section formulaire
# 3. Clic → Drawer s'ouvre avec 12 repos affichés
# 4. Filtre "Framework" → 3 repos (Superpowers, Loki Mode, GSD)
# 5. Clic "Ajouter" sur un repo → apparaît dans la liste repos du formulaire
# 6. Fermer le Drawer → repos ajoutés persistent dans le formulaire
# 7. Soumettre le job → fonctionne exactement comme avant
```

---

## Fichiers à lire avant de commencer

```
# Page existante (LIRE EN ENTIER avant de modifier)
mvp/frontend/src/app/(dashboard)/skill-seekers/page.tsx

# Types existants (pour cohérence)
mvp/frontend/src/features/skill-seekers/types.ts

# Référence pattern MUI dans le projet
mvp/frontend/src/features/transcription/  (pour style MUI)
```
