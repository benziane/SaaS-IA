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
    description: "CLI officiel de coding agentic d'Anthropic",
    category: 'official',
    stars: 82500,
    score: 10,
    tags: ['Terminal', 'Agentic', 'TypeScript'],
    ghUrl: 'https://github.com/anthropics/claude-code',
  },
  {
    repo: 'anthropics/claude-cookbooks',
    name: 'Claude Cookbooks',
    description: "Notebooks Jupyter et recettes pratiques pour l'API Claude",
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
    description: "Répertoire d'agents, hooks, plugins et outils Claude Code",
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
    description: '161 règles design IA — 67+ styles, 161 palettes',
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
