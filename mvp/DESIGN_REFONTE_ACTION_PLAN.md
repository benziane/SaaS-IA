# Plan d'Action - Refonte Design SaaS-IA

> **Date** : 2026-03-24 (mis a jour : relecture complete)
> **Source** : Consolidation de 3 recherches (Perplexity Pro + ChatGPT Browsing + Claude Deep Research)
> **Document source** : `design-hub/docs/Design Systems et Architectures Frontend pour 2026.md` (2300+ lignes, 77+ sources)
> **Statut** : Plan valide, pret a executer
> **Prerequis** : Audit complete dans DESIGN_SYSTEM_AUDIT.md

---

## Decisions prises

| Decision | Choix | Justification |
|----------|-------|---------------|
| UI Library | **shadcn/ui** | 93% score audit, 100% compat design-hub |
| Headless | **Radix UI** (court terme), evaluer **Ark UI** (moyen terme) | Radix = mature + shadcn natif |
| Styling | **Tailwind CSS v3.4** → **v4** (progressif) | CSS-first config, perf x3-x10 |
| Icons | **Lucide React** (via @design-hub/icons) | Unifie 3 systemes actuels |
| Fonts | **Inter + JetBrains Mono** (via @design-hub/fonts) | Remplace Public Sans |
| Charts | **Recharts** (unifie, drop MUI X-Charts) | Deja en place, theming CSS vars |
| Animations | **Framer Motion** + **View Transitions API** (pages) | FM = composants, VTA = navigation |
| Forms | **React Hook Form + Zod** (conserver) | Mature, shadcn-natif |
| State | **TanStack Query + Zustand** (conserver) | Pas de changement |
| Tokens | **DTCG 3-couches** via **Style Dictionary** | Primitives → Semantic → Component |
| Versioning | **Changesets** dans monorepo pnpm | Standard monorepo 2026 |
| Visual regression | **Playwright screenshots** | Gratuit, deja en stack |
| Command palette | **cmdk** (via shadcn) | Remplace custom CommandPalette |
| URL state | **nuqs** | Tabs persistants, filtres, presets |
| Virtualisation | **@tanstack/react-virtual** | Chat, logs, tables 1000+ rows |
| Pipeline builder | **@xyflow/react** + **dagre/elkjs** | Auto-layout DAG |
| Streaming markdown | **streamdown** (Vercel) | Zero-flicker, block-level parsing |
| AI SDK | **Vercel AI SDK** (`ai`) | Streaming, tool calls, agents |

---

## Technologies emergentes - Verdicts

| Techno | Verdict | Action |
|--------|---------|--------|
| **Tailwind v4** | Adopter progressivement | Design-hub d'abord, app ensuite |
| **UnoCSS** | Ignorer | TW v4 comble l'ecart, ecosysteme trop petit |
| **Panda CSS** | Complementaire seulement | Possible pour @design-hub/components, pas pour l'app |
| **React 19 + Next.js 16** | Attendre stabilisation | Refonte DS en React 18, upgrade apres |
| **Ark UI** | Evaluer moyen terme | Tester sur composants manquants de Radix |
| **Park UI** | Surveiller | Alternative future a shadcn si Ark UI mature |
| **Open UI standards** | Surveiller | Aucune action immediate |
| **View Transitions API** | Adopter pour navigation | Remplace FM pour transitions de pages |
| **CSS Anchor Positioning** | Surveiller | Laisser Radix l'integrer sous le capot |
| **Signals (TC39)** | Veille | Garder TanStack Query + Zustand |

---

## Phase 0 : Foundation (J1-J3)

### 0.1 Installer shadcn/ui + design-hub packages

- [ ] `npx shadcn@latest init` (configurer avec Tailwind + CSS vars)
- [ ] `npm install @design-hub/tokens-core @design-hub/fonts @design-hub/utils @design-hub/icons @design-hub/configs`
- [ ] Configurer `tailwind.config.ts` avec tokens-core preset + configs base-preset
- [ ] Ajouter `@import '@design-hub/fonts/css'` + `@import '@design-hub/tokens-core/css'` dans globals.css
- [ ] Mapper les CSS vars shadcn sur les tokens design-hub
- [ ] Configurer `next-themes` pour theme switching

### 0.2 Unifier les systemes d'icones

- [ ] Remplacer tous les imports `@mui/icons-material` → `import { X } from '@design-hub/icons'`
- [ ] Supprimer le CDN Boxicons de layout.tsx
- [ ] Supprimer `@iconify/*` des devDependencies
- [ ] Mettre a jour le CommandPalette pour utiliser Lucide

### 0.3 Unifier les utilitaires CSS

- [ ] Remplacer `clsx` + `tailwind-merge` separees → `import { cn } from '@design-hub/utils'`
- [ ] Remplacer la font Public Sans → Inter (via @design-hub/fonts)
- [ ] Creer le fichier de couleurs semantiques (mapping MUI palette → CSS vars)

### 0.4 Installer les nouvelles libs

- [ ] `npm install cmdk nuqs @tanstack/react-virtual streamdown next-themes`
- [ ] `npm install @xyflow/react dagre` (pour pipeline builder)

---

## Phase 1 : Core Layout (J3-J7)

### 1.1 Nouveau shell dashboard

- [ ] Creer le layout shadcn : Sidebar collapsible + Header + Breadcrumbs
- [ ] Implementer la navigation Hub & Spoke (6 categories max pour 25 modules)
- [ ] Structure navigation recommandee :

```
📊 Dashboard (home)
🤖 IA & Agents
   ├── Chat
   ├── Agents
   ├── Crews
   ├── Realtime
🔧 Outils & Pipelines
   ├── Transcription / YouTube
   ├── Pipelines
   ├── Workflows
   ├── Compare
📝 Contenu & Media
   ├── Content Studio
   ├── Images
   ├── Video Studio
   ├── Voice
📚 Donnees & Knowledge
   ├── Knowledge Base
   ├── Data Analyst
   ├── Crawler
   ├── Sentiment
   ├── Search
🛡️ Securite & Monitoring
   ├── Security Guardian
   ├── AI Monitoring
   ├── Costs
   ├── Memory
⚙️ Configuration
   ├── Fine-Tuning
   ├── Workspaces
   ├── Billing
   ├── API Keys
   ├── Profile
```

### 1.2 Command palette (cmdk)

- [ ] Migrer CommandPalette.tsx vers shadcn `<Command>` (cmdk)
- [ ] Exposer les modules comme "capacites" (pas juste des pages)
- [ ] Actions rapides : "Transcrire une video", "Creer un workflow", "Comparer des modeles"
- [ ] Favoris/recents en haut de la palette

### 1.3 Navigation avancee

- [ ] URL state avec `nuqs` (filtres, tabs, layout grid/list persistants)
- [ ] Breadcrumbs dynamiques generes depuis les routes App Router
- [ ] Favoris/bookmarks utilisateur persistants (localStorage)

---

## Phase 2 : Pages prioritaires (J7-J14)

### 2.1 Dashboard principal

- [ ] KPI cards avec sparklines (Recharts + tokens CSS vars)
- [ ] Hook `useChartColors()` qui lit les CSS vars pour palette adaptee au theme
- [ ] Palette semantique charts : `--chart-1` a `--chart-8` dans les tokens
- [ ] Stats temps reel : requetes/s, latence, cout/1k tokens

### 2.2 Chat IA

- [ ] Migrer vers `streamdown` pour le rendu markdown streaming (zero flicker)
- [ ] Double buffer : raw (texte complet) + displayed (blocs stabilises)
- [ ] Virtualisation des messages avec `@tanstack/react-virtual`
- [ ] `aria-live="polite"` pour screen readers
- [ ] Composant shadcn : ScrollArea + ResizablePanel + Sheet (sources RAG)
- [ ] Citations RAG cliquables → source panel (document, chunk, score)
- [ ] Feedback loop : 👍/👎 + correction + export dataset

### 2.3 Knowledge Base

- [ ] Shadcn DataTable (TanStack Table) pour documents
- [ ] Dropzone shadcn pour upload
- [ ] Panel lateral pour chunks/embeddings

### 2.4 Transcription

- [ ] Player audio avec waveform (wavesurfer.js, lazy-loaded)
- [ ] Timeline speaker diarization
- [ ] Export multi-format

### 2.5 Agents

- [ ] Timeline d'execution facon Langfuse (step-by-step cliquable)
- [ ] Chaque tool call = step avec temps, cout, inputs/outputs
- [ ] Progress multi-etapes avec icones Lucide

---

## Phase 3 : Pages secondaires (J14-J21)

### 3.1 Pipeline Builder

- [ ] Noeuds custom shadcn dans @xyflow/react (cards, badges, menus)
- [ ] "Node UI spec" : header (icon+titre+status) / body (inputs) / footer (handles+actions)
- [ ] Handles colores par type de donnees (embedding, texte, audio, image)
- [ ] Auto-layout avec dagre/elkjs
- [ ] Panneau config lateral (tabs: Node / Pipeline / Logs)
- [ ] Snap-to-grid + undo/redo

### 3.2 Compare (multi-model)

- [ ] Layout side-by-side avec memes prompts
- [ ] Metriques : tokens, cout, latence, qualite
- [ ] Voting ELO + feedback

### 3.3 Content Studio

- [ ] Preview multi-format (blog, social, newsletter)
- [ ] Score lisibilite (Flesch-Kincaid via textstat backend)

### 3.4 Workflows (DAG editor)

- [ ] Meme pattern que Pipeline Builder (XYFlow)
- [ ] Node templates par type d'action (LLM, tool, branch, RAG)

### 3.5 Crews

- [ ] Cards par agent avec role, status, inter-communication
- [ ] Timeline collaborative

---

## Phase 4 : Pages restantes (J21-J26)

### 4.1 Data Analyst

- [ ] Upload zone + DuckDB SQL results
- [ ] Charts generes par IA (Recharts + palette semantique)
- [ ] Separation viz (resume) vs table (preuve, virtualisee)

### 4.2 Media (Images / Video / Voice)

- [ ] Galerie images avec lazy-load
- [ ] Video player avec Monaco pour scripts
- [ ] Waveform pour voice clone (wavesurfer.js)

### 4.3 Fine-Tuning

- [ ] Wizard multi-etapes (dataset → config → training → eval)
- [ ] Progress bar training temps reel

### 4.4 Security / Monitoring / Memory / Search

- [ ] LiveLog + TraceTimeline pour monitoring
- [ ] Terminal-like pour logs temps reel (xterm.js, lazy)
- [ ] Dashboard securite avec audit trail

### 4.5 Admin (Billing / Profile / API Keys / Costs)

- [ ] Settings layout standardise
- [ ] ParameterRow reutilisable (label, description, control, reset-to-default)

---

## Phase 5 : Cleanup + QA (J26-J28)

### 5.1 Supprimer MUI

- [ ] Desinstaller `@mui/material` `@mui/icons-material` `@mui/lab` `@mui/x-charts` `@mui/material-nextjs`
- [ ] Desinstaller `@emotion/react` `@emotion/styled` `@emotion/cache`
- [ ] Supprimer le dossier `src/@core/` (Sneat theme)
- [ ] Supprimer le dossier `src/@menu/` (Sneat navigation)
- [ ] Supprimer le dossier `src/@layouts/` (Sneat layouts)
- [ ] Supprimer `src/components/theme/mergedTheme.ts` et overrides
- [ ] Nettoyer `src/configs/themeConfig.ts`
- [ ] Supprimer `stylis-plugin-rtl` `react-perfect-scrollbar`

### 5.2 Audit qualite

- [ ] Audit bundle size (objectif < 100 KB UI framework)
- [ ] Playwright visual regression sur pages critiques
- [ ] Tests E2E sur flows principaux (chat, transcription, pipelines)
- [ ] Audit accessibilite axe-core sur 10 pages cles
- [ ] Lighthouse perf audit (objectif > 90)

---

## Evolution design-hub (en parallele)

### Tokens : Primitives → Semantic → Component

- [ ] Ajouter `tokens/semantic/{light,dark}.json` avec aliases DTCG
- [ ] Ajouter `tokens/components/{button,input,card,chat,node}.json`
- [ ] Migrer pipeline generate.mjs vers Style Dictionary v4
- [ ] Generer CSS vars par theme : `[data-theme="x-dark"]`
- [ ] Ajouter Oklch pour palettes uniformes en perception
- [ ] Validation CI : schema JSON + nommage + breaking changes

### Nouveau package : @design-hub/components

- [ ] Creer `shared/components/` dans le monorepo
- [ ] Composants primitifs : Button, Input, Select, Dialog, Sheet, Tabs, Toast, Command, DataTable
- [ ] Composants layout : AppShell, Sidebar, PageHeader, Breadcrumbs, SplitPane
- [ ] Composants IA : ChatLayout, AgentTimeline, PipelineNode, ModelCompareView, PromptEditor, RAGSourceList
- [ ] Stories Storybook + tests a11y pour chaque composant
- [ ] CVA recipes pour toutes les variantes

### Multi-theme industriel

- [ ] Formaliser les 43 themes comme modes DTCG
- [ ] Theme Registry (manifest JSON avec metadata, contrast score)
- [ ] Theme Playground dans l'Explorer (picker couleur → palette Oklch → export JSON + Tailwind preset)
- [ ] Lazy-load des feuilles CSS par theme (pas 43 themes dans le bundle)

### Distribution

- [ ] Ajouter `@changesets/cli` au monorepo
- [ ] Convention de commit + PR sans changeset = bloque
- [ ] Release pipeline : publish npm + tag Git + changelog
- [ ] Release train mensuel + hotfix si besoin

---

## Repos de reference a consulter

### Templates admin shadcn

| Repo | Stars | Utilite |
|------|-------|---------|
| shadcn-admin (satnaing) | 11K+ | Layout admin complet, 10+ pages |
| next-shadcn-dashboard-starter (Kiranism) | 6K+ | Dashboard starter App Router |
| awesome-shadcn-ui (bytefer/birobirobiro) | 15K+ | Index de tous les projets shadcn |

### Composants IA

| Repo | Stars | Utilite |
|------|-------|---------|
| Vercel AI SDK (`ai`) | 23K+ | Streaming, tool calls, agents |
| assistant-ui | 2K+ | Primitives chat IA haut de gamme |
| streamdown (Vercel) | Nouveau | Markdown streaming sans flicker |
| LibreChat | 33K+ | Reference UI chat multi-model |
| Open WebUI | 128K+ | UI IA self-hosted la plus populaire |
| Langfuse | 23K+ | Observabilite LLM, traces, evals |

### Outils visuels

| Repo | Stars | Utilite |
|------|-------|---------|
| xyflow (React Flow) | 36K+ | Pipeline/DAG builder |
| monaco-editor | 46K+ | Editeur code (prompt, SQL, config) |
| xterm.js | 20K+ | Terminal web (logs live) |
| wavesurfer.js | 10K+ | Waveform audio |
| cmdk | 12K+ | Command palette |
| nuqs | 10K+ | URL state management |

### Design system tooling

| Repo | Stars | Utilite |
|------|-------|---------|
| style-dictionary (amzn) | 4.6K+ | Token transformation |
| Storybook | 90K+ | Doc + test composants |
| Playwright | 85K+ | Visual regression testing |
| Changesets | 12K+ | Versioning monorepo |

---

## Astuces killer a implementer

### 1. Hook `useChartColors()`

```tsx
function useChartColors() {
  const style = getComputedStyle(document.documentElement);
  return Array.from({ length: 8 }, (_, i) =>
    style.getPropertyValue(`--chart-${i + 1}`).trim()
  );
}
```

Partage la meme palette entre Recharts, sparklines, et composants shadcn.

### 2. Composant ParameterRow

```tsx
// Reutiliser partout : agents, RAG, finetuning, guardrails, workflows
<ParameterRow
  label="Temperature"
  description="Controls randomness (0-2)"
  control={<Slider min={0} max={2} step={0.1} />}
  resetValue={0.7}
  docsLink="/docs/temperature"
/>
```

### 3. Layout Contract par route segment

```
app/(shell)/             → Shell commun (sidebar + header + breadcrumbs)
app/(shell)/chat/        → Chat layout (sidebar conversations + main)
app/(shell)/pipelines/   → Builder layout (canvas + config panel)
app/(shell)/settings/    → Settings layout (sidebar nav + content)
```

### 4. Streaming markdown sans flicker

```tsx
// streamdown : parse par blocs complets (pas par caractere)
// + ligne fantome "en cours" remplacee quand bloc complet
// + useDeferredValue pour lisser les updates
import { Streamdown } from 'streamdown';
```

### 5. Theme switching sans flash

```tsx
// Script inline dans <head> (avant hydration)
<script dangerouslySetInnerHTML={{ __html: `
  (function() {
    var theme = localStorage.getItem('theme') || 'system';
    if (theme === 'system') {
      theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    document.documentElement.setAttribute('data-theme', theme);
  })()
` }} />
```

---

## Metriques de succes

| Metrique | Avant (MUI) | Objectif (shadcn) | Mesure |
|----------|-------------|-------------------|--------|
| Bundle JS UI | ~350 KB | < 100 KB | `next build --analyze` |
| Packages UI | 18 | 3-5 | `package.json` |
| Fichiers theme | 37+ overrides | 1 globals.css | Count files |
| Couches styling | 3 | 1 (Tailwind) | Architecture |
| Systemes icones | 3 | 1 (Lucide) | Imports count |
| Libs charts | 2 | 1 (Recharts) | `package.json` |
| First paint | ~2.5s | < 1.5s | Lighthouse |
| Lighthouse perf | ~75 | > 90 | Lighthouse |
| A11y score | ~80 | > 95 | axe-core |
| Dark mode flash | Oui | Non | Visual test |

---

---

## COMPLEMENT : Insights additionnels (relecture approfondie)

### Libs supplementaires identifiees (non mentionnees precedemment)

| Lib | Stars | Role | Source | Priorite |
|-----|-------|------|--------|----------|
| `assistant-ui` | 2K+ | **Primitives chat IA haut de gamme** : appels d'outils, citations, streaming avance | Recherche 2 (Gemini) | Phase 2 |
| `@formkit/auto-animate` | 14K+ | Micro-animations automatiques zero-config pour listes dynamiques (chat, jobs, logs) | Recherche 1 (Perplexity) | Phase 2 |
| `@tremor/react` | 4.5K+ | Composants dashboard Tailwind-first (KPI cards, charts, metrics) — complementaire a Recharts | Recherche 1+3 | Phase 2 |
| `react-diff-viewer-continued` | - | Diff de textes/code pour comparaison de sorties multi-modeles | Recherche 1 | Phase 3 |
| `elkjs` | 2.5K+ | Algorithmes de layout avances pour DAG (ports, dataflow) — plus precis que dagre | Recherche 2 (Deep) | Phase 3 |
| `@auto-animate` | 14K+ | Transitions auto listes/inserts/reorder avec 1 attribut | Recherche 1 | Phase 1 |
| `turborepo` | 25K+ | Accelerer builds/tests dans le monorepo design-hub (cache + parallelisation) | Recherche 3 | Design-hub |

### Pattern UIBridge — Strategie de migration recommandee

Mentionnee par la **Recherche 1 (Perplexity)** comme astuce killer pour la migration MUI → shadcn :

```tsx
// src/lib/ui-bridge.ts
// Facade qui re-exporte soit MUI soit shadcn pour un set de composants

// Phase 1 : pointe vers MUI
export { Button } from '@mui/material';
export { Dialog } from '@mui/material';
export { TextField as Input } from '@mui/material';

// Phase 2 : on migre composant par composant
export { Button } from '@/components/ui/button';      // shadcn
export { Dialog } from '@/components/ui/dialog';       // shadcn
export { TextField as Input } from '@mui/material';    // encore MUI

// Phase finale : tout pointe vers shadcn
export { Button } from '@/components/ui/button';
export { Dialog } from '@/components/ui/dialog';
export { Input } from '@/components/ui/input';
```

**Avantage** : le code applicatif importe toujours depuis `@/lib/ui-bridge`, jamais directement MUI ou shadcn. La migration est invisible pour les pages.

### Component Mapping Manifest (codemod-ready)

Mentionnee par la **Recherche 2 (Deep Research)** :

```yaml
# component-mapping.yaml — base pour codemods automatiques
mappings:
  - mui: "Button"
    shadcn: "Button"
    import_from: "@/components/ui/button"
    props_map:
      variant: { contained: "default", outlined: "outline", text: "ghost" }
      color: { primary: "default", error: "destructive", inherit: "secondary" }
      startIcon: "→ children avec <Icon /> avant le texte"

  - mui: "TextField"
    shadcn: "Input"
    import_from: "@/components/ui/input"
    props_map:
      variant: { outlined: "default", standard: "default" }
      multiline: "→ utiliser Textarea au lieu de Input"
      helperText: "→ FormDescription dans un FormField"

  - mui: "Dialog"
    shadcn: "Dialog"
    import_from: "@/components/ui/dialog"
    children_map:
      DialogTitle: "DialogHeader > DialogTitle"
      DialogContent: "DialogContent (direct)"
      DialogActions: "DialogFooter"

  - mui: "Chip"
    shadcn: "Badge"
    import_from: "@/components/ui/badge"
    props_map:
      color: { primary: "default", error: "destructive", success: "outline" }

  - mui: "CircularProgress"
    shadcn: "Loader2 (Lucide) avec animate-spin"
    import_from: "lucide-react"

  - mui: "LinearProgress"
    shadcn: "Progress"
    import_from: "@/components/ui/progress"

  - mui: "Grid"
    shadcn: "div avec classes Tailwind grid/flex"
    notes: "Grid container → 'grid grid-cols-12 gap-4', Grid item xs={6} → 'col-span-6'"

  - mui: "Stack"
    shadcn: "div avec classes Tailwind flex"
    notes: "Stack direction=column → 'flex flex-col gap-*'"

  - mui: "Box"
    shadcn: "div + Tailwind"
    notes: "Remplacer sx={{}} par className='...'"

  - mui: "Typography"
    shadcn: "HTML semantique + Tailwind"
    notes: "variant=h1 → <h1 className='text-3xl font-bold'>"
```

### Patterns UI IA specifiques a ne pas manquer

Extraites des 3 recherches, ces patterns sont **cruciales pour une plateforme IA 2026** :

#### 1. Agent Execution Timeline (pattern Langfuse)

```
┌─ Step 1: Retrieve documents (RAG)          ⏱ 245ms  $0.001 ──┐
│   └─ Input: "How to configure pipelines"                      │
│   └─ Output: 3 chunks (scores: 0.92, 0.87, 0.81)             │
├─ Step 2: Call LLM (Gemini 2.0 Flash)       ⏱ 1.2s   $0.003 ──┤
│   └─ Tokens: 1,240 in / 450 out                               │
│   └─ Temperature: 0.7                                         │
├─ Step 3: Tool Call (create_pipeline)       ⏱ 89ms   $0.000 ──┤
│   └─ Status: ✅ Success                                       │
│   └─ Result: Pipeline ID: pip_abc123                           │
└─ Total                                     ⏱ 1.5s   $0.004 ──┘
```

Chaque step = composant cliquable → panneau lateral avec inputs/outputs complets.

#### 2. Context Window Visualizer

```
┌─────────────────────────────────────────────────────┐
│ ██████████████████████░░░░░░░░░░░░░ 65% utilise     │
│                                                      │
│ System prompt     ████      2,100 tokens  (16%)      │
│ RAG context       ██████    3,800 tokens  (29%)      │
│ Conversation      ██████    4,200 tokens  (32%)      │
│ Available         ░░░░░     4,900 tokens  (35%)      │
│                                                      │
│ Model: Gemini 2.0 Flash  Max: 15,000 tokens          │
└─────────────────────────────────────────────────────┘
```

#### 3. RAG Source Citations (pattern "pro")

Chaque reponse IA affiche ses sources avec score de pertinence :

```
[1] pipeline_guide.md (chunk 3/12) — Score: 0.92 — "Les pipelines..."  [Voir ▸]
[2] api_reference.md (chunk 7/45)  — Score: 0.87 — "POST /pipelines..." [Voir ▸]
```

Clic sur [Voir ▸] → panel lateral avec le document complet, chunk surligne.

#### 4. Model Comparison Side-by-Side

```
┌──────────────────────┬──────────────────────┬──────────────────────┐
│ Gemini 2.0 Flash     │ Claude Sonnet        │ Groq Llama 3.3      │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ ⏱ 1.2s               │ ⏱ 2.1s               │ ⏱ 0.4s               │
│ 💰 $0.003             │ 💰 $0.008             │ 💰 $0.001             │
│ 📊 450 tokens         │ 📊 620 tokens         │ 📊 380 tokens         │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ [Response...]        │ [Response...]        │ [Response...]        │
│                      │                      │                      │
│ 👍 3  👎 1            │ 👍 5  👎 0            │ 👍 2  👎 2            │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

#### 5. Prompt Editor avec variables

```
┌─────────────────────────────────────────────────┐
│ Prompt Editor                           [Preview]│
├─────────────────────────────────────────────────┤
│ Tu es un assistant {{role}} specialise en        │
│ {{domain}}. Reponds en {{language}}.             │
│                                                  │
│ Contexte: {{rag_context}}                        │
│                                                  │
│ Question: {{user_input}}                         │
├─────────────────────────────────────────────────┤
│ Variables:                                       │
│ ┌─ role: [Expert technique    ▾]                │
│ ├─ domain: [Intelligence Artificielle]          │
│ ├─ language: [Francais ▾]                       │
│ ├─ rag_context: [Auto-inject from KB ✓]        │
│ └─ user_input: [Bound to chat input ✓]         │
└─────────────────────────────────────────────────┘
```

### Tokens semantiques — Schema DTCG recommande (consolidation 3 sources)

Les 3 sources convergent sur cette architecture :

```json
{
  "$schema": "https://design-tokens.github.io/community-group/format/",

  "primitives": {
    "color": {
      "blue": {
        "50":  { "$value": "oklch(0.97 0.01 250)", "$type": "color" },
        "500": { "$value": "oklch(0.55 0.18 250)", "$type": "color" },
        "900": { "$value": "oklch(0.25 0.12 250)", "$type": "color" }
      },
      "gray": {
        "50":  { "$value": "oklch(0.98 0.00 0)", "$type": "color" },
        "950": { "$value": "oklch(0.13 0.00 0)", "$type": "color" }
      }
    },
    "space": {
      "1": { "$value": "0.25rem", "$type": "dimension" },
      "4": { "$value": "1rem", "$type": "dimension" },
      "8": { "$value": "2rem", "$type": "dimension" }
    }
  },

  "semantic": {
    "color": {
      "bg": {
        "canvas":   { "$value": "{primitives.color.gray.50}", "$type": "color",
                      "$extensions": { "mode": { "dark": "{primitives.color.gray.950}" } } },
        "surface":  { "$value": "white", "$type": "color",
                      "$extensions": { "mode": { "dark": "{primitives.color.gray.900}" } } },
        "elevated": { "$value": "white", "$type": "color",
                      "$extensions": { "mode": { "dark": "{primitives.color.gray.800}" } } }
      },
      "text": {
        "primary":  { "$value": "{primitives.color.gray.950}", "$type": "color",
                      "$extensions": { "mode": { "dark": "{primitives.color.gray.50}" } } },
        "muted":    { "$value": "{primitives.color.gray.500}", "$type": "color" }
      },
      "accent": {
        "primary":  { "$value": "{primitives.color.blue.500}", "$type": "color" }
      },
      "border": {
        "default":  { "$value": "{primitives.color.gray.200}", "$type": "color",
                      "$extensions": { "mode": { "dark": "{primitives.color.gray.700}" } } }
      },
      "chart": {
        "1": { "$value": "{primitives.color.blue.500}", "$type": "color" },
        "2": { "$value": "oklch(0.65 0.20 150)", "$type": "color" },
        "3": { "$value": "oklch(0.65 0.20 30)", "$type": "color" }
      }
    }
  },

  "components": {
    "button": {
      "primary": {
        "bg":     { "$value": "{semantic.color.accent.primary}", "$type": "color" },
        "text":   { "$value": "white", "$type": "color" },
        "radius": { "$value": "{primitives.radius.md}", "$type": "dimension" }
      }
    },
    "card": {
      "bg":      { "$value": "{semantic.color.bg.surface}", "$type": "color" },
      "border":  { "$value": "{semantic.color.border.default}", "$type": "color" },
      "shadow":  { "$value": "{primitives.shadow.sm}", "$type": "shadow" }
    },
    "chat-message": {
      "user-bg":      { "$value": "{semantic.color.accent.primary}", "$type": "color" },
      "assistant-bg": { "$value": "{semantic.color.bg.elevated}", "$type": "color" }
    }
  }
}
```

**Pourquoi Oklch** (mentionne par les 3 sources) : les rampes de couleurs en Oklch ont une luminosite perceptuellement uniforme, contrairement a HSL. Resultat : le dark mode ne produit pas de decalages de contraste surprises.

### Monorepo template de reference

La **Recherche 3 (Perplexity)** a identifie un repo directement pertinent :

- **[turborepo-shadcn-nextjs](https://github.com/gmickel/turborepo-shadcn-nextjs)** : template Turborepo + Next.js + Nextra (docs) + Storybook + package `@ui` shadcn partage. Architecture directement applicable a notre design-hub → SaaS-IA.

### References additionnelles confirmees

| Source | Lien | Pertinence |
|--------|------|------------|
| Martin Fowler - Design Token Architecture | martinfowler.com/articles/design-token-based-ui-architecture.html | Article fondamental sur tokens 3 couches |
| DTCG Spec officielle (stable v1) | designtokens.org | Format standard, implementations Style Dictionary + Tokens Studio |
| Design Tokens Course (Brad Frost) | designtokenscourse.com | Formation de reference par le createur d'Atomic Design |
| Material Design 3 - Design Tokens | m3.material.io/foundations/design-tokens | Reference Google pour l'architecture tokens |
| Coder MUI→shadcn migration (issue #18993) | github.com/coder/coder/issues/18993 | Retour d'experience reel d'une migration a grande echelle |
| shadcn monorepo guide | ui.shadcn.com/docs/monorepo | Guide officiel pour integrer shadcn dans un monorepo |

### Points d'attention supplementaires (risques identifies)

| Risque | Source | Mitigation |
|--------|--------|------------|
| Templates shadcn top-starred sont en **React 19** (pas 18) | Deep Research | Les utiliser comme **reference d'architecture**, pas comme copy-paste direct |
| **Open WebUI** licence "Other/NOASSERTION" | Deep Research | Verifier licence avant de s'en inspirer pour du code |
| Tailwind v4 a des **contraintes navigateurs** (Safari 16.4+, Chrome 111+, Firefox 128+) | Deep Research | Verifier les navigateurs cibles de nos utilisateurs avant migration |
| Style Dictionary a des **breaking changes** recents + exigence Node LTS | Deep Research | Tester sur Node 22 LTS, suivre le changelog |
| **CVE-2025-55182** sur React 19/Next 16 RSC | Recherche 1 | Raison supplementaire de rester sur React 18 pour la refonte |
| `tldraw` necessite une **licence payante** pour usage production | Deep Research | Exclure, utiliser React Flow uniquement |
| Tailwind Labs a **licencie 75%** de leur equipe engineering | Recherche 3 (HN ref) | Risque ecosysteme — surveiller, mais TW v4 est deja sorti |

### Checklist de validation pre-migration

Avant de lancer la Phase 0, verifier :

- [ ] Navigateurs cibles supportent Tailwind v4 ? (Safari 16.4+, Chrome 111+, Firefox 128+)
- [ ] Node.js ≥ 22 LTS installe pour Style Dictionary v4
- [ ] design-hub packages buildent correctement (`pnpm build`)
- [ ] Tokens CSS vars generes et valides
- [ ] shadcn init fonctionne dans le monorepo (voir guide officiel monorepo)
- [ ] MUI et shadcn coexistent sans conflit CSS dans une page test
- [ ] Playwright et axe-core fonctionnent pour baseline screenshots

---

> **Conclusion** : Ce plan consolide les recommandations de 3 recherches independantes (77+ sources, 2300+ lignes) en actions concretes. La refonte est ambitieuse mais structuree en 5 phases progressives avec coexistence MUI/shadcn. L'alignement parfait entre shadcn/ui et design-hub est le multiplicateur de valeur principal. Les patterns IA specifiques (Agent Timeline, Context Visualizer, RAG Citations, Prompt Editor) sont les differenciateurs qui transformeront notre plateforme d'un "dashboard classique" en un "hub d'orchestration IA de 2026".
