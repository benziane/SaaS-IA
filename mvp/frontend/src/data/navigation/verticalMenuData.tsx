// Type Imports
import type { VerticalMenuDataType } from '@/types/menuTypes'

/**
 * Vertical Menu Data - SaaS-IA
 *
 * 42 backend modules grouped into 9 functional categories.
 * Structure mirrors ModuleRegistry auto-discovery on the backend.
 */
const verticalMenuData = (): VerticalMenuDataType[] => [
  // ─── Overview ────────────────────────────────────────────────
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: 'tabler:layout-dashboard',
  },

  // ─── AI CORE ─────────────────────────────────────────────────
  {
    label: 'AI CORE',
    isSection: true,
  },
  {
    label: 'Agents',
    href: '/agents',
    icon: 'tabler:robot',
  },
  {
    label: 'Multi-Agent Crew',
    href: '/crews',
    icon: 'tabler:users',
  },
  {
    label: 'AI Memory',
    href: '/memory',
    icon: 'tabler:brain',
  },
  {
    label: 'AI Compare',
    href: '/compare',
    icon: 'tabler:arrows-diff',
  },

  // ─── CREATE ──────────────────────────────────────────────────
  {
    label: 'CREATE',
    isSection: true,
  },
  {
    label: 'Content Studio',
    href: '/content-studio',
    icon: 'tabler:pencil',
  },
  {
    label: 'Image Gen',
    href: '/images',
    icon: 'tabler:photo',
  },
  {
    label: 'Video Gen',
    href: '/video-studio',
    icon: 'tabler:movie',
  },
  {
    label: 'Audio Studio',
    href: '/audio-studio',
    icon: 'tabler:wavesaw-mono',
  },
  {
    label: 'Presentations',
    href: '/presentations',
    icon: 'tabler:presentation',
  },
  {
    label: 'Voice Clone',
    href: '/voice',
    icon: 'tabler:microphone-2',
  },

  // ─── ANALYZE ─────────────────────────────────────────────────
  {
    label: 'ANALYZE',
    isSection: true,
  },
  {
    label: 'Data Analyst',
    href: '/data',
    icon: 'tabler:chart-bar',
  },
  {
    label: 'Sentiment',
    href: '/sentiment',
    icon: 'tabler:mood-smile',
  },
  {
    label: 'AI Monitoring',
    href: '/monitoring',
    icon: 'tabler:activity',
  },
  {
    label: 'Cost Tracker',
    href: '/costs',
    icon: 'tabler:coin',
  },

  // ─── KNOWLEDGE ───────────────────────────────────────────────
  {
    label: 'KNOWLEDGE',
    isSection: true,
  },
  {
    label: 'Web Crawler',
    href: '/crawler',
    icon: 'tabler:world-download',
  },
  {
    label: 'Transcription',
    href: '/transcription',
    icon: 'tabler:player-record',
  },
  {
    label: 'YouTube',
    href: '/youtube',
    icon: 'tabler:brand-youtube',
  },
  {
    label: 'PDF Processor',
    href: '/pdf',
    icon: 'tabler:file-type-pdf',
  },
  {
    label: 'Knowledge Base',
    href: '/knowledge',
    icon: 'tabler:books',
  },

  // ─── ENGAGE ──────────────────────────────────────────────────
  {
    label: 'ENGAGE',
    isSection: true,
  },
  {
    label: 'Chat',
    href: '/chat',
    icon: 'tabler:message-chatbot',
  },
  {
    label: 'Chatbot Builder',
    href: '/chatbots',
    icon: 'tabler:robot-face',
  },
  {
    label: 'Realtime AI',
    href: '/realtime',
    icon: 'tabler:broadcast',
  },
  {
    label: 'AI Forms',
    href: '/forms',
    icon: 'tabler:forms',
  },

  // ─── AUTOMATE ────────────────────────────────────────────────
  {
    label: 'AUTOMATE',
    isSection: true,
  },
  {
    label: 'Workflows',
    href: '/workflows',
    icon: 'tabler:git-merge',
  },
  {
    label: 'Pipelines',
    href: '/pipelines',
    icon: 'tabler:git-branch',
  },
  {
    label: 'Integrations',
    href: '/integrations',
    icon: 'tabler:plug',
  },
  {
    label: 'Social Publisher',
    href: '/social',
    icon: 'tabler:share',
  },

  // ─── BUILD ───────────────────────────────────────────────────
  {
    label: 'BUILD',
    isSection: true,
  },
  {
    label: 'Code Sandbox',
    href: '/sandbox',
    icon: 'tabler:terminal-2',
  },
  {
    label: 'Repo Analyzer',
    href: '/repo-analyzer',
    icon: 'tabler:git-fork',
  },
  {
    label: 'Skill Seekers',
    href: '/skill-seekers',
    icon: 'tabler:brand-github',
  },
  {
    label: 'Fine-Tuning',
    href: '/fine-tuning',
    icon: 'tabler:adjustments',
  },

  // ─── SEARCH ──────────────────────────────────────────────────
  {
    label: 'SEARCH',
    isSection: true,
  },
  {
    label: 'Unified Search',
    href: '/search',
    icon: 'tabler:search',
  },
  {
    label: 'Marketplace',
    href: '/marketplace',
    icon: 'tabler:shopping-bag',
  },

  // ─── PLATFORM ────────────────────────────────────────────────
  {
    label: 'PLATFORM',
    isSection: true,
  },
  {
    label: 'Workspaces',
    href: '/workspaces',
    icon: 'tabler:layout-grid',
  },
  {
    label: 'Billing',
    href: '/billing',
    icon: 'tabler:credit-card',
  },
  {
    label: 'API Keys',
    href: '/api-docs',
    icon: 'tabler:key',
  },
  {
    label: 'Feature Flags',
    href: '/feature-flags',
    icon: 'tabler:flag',
  },
  {
    label: 'Tenants',
    href: '/tenants',
    icon: 'tabler:building',
  },
  {
    label: 'Security',
    href: '/security',
    icon: 'tabler:shield-lock',
  },
  {
    label: 'Secrets',
    href: '/secrets',
    icon: 'tabler:lock',
  },
  {
    label: 'Modules',
    href: '/modules',
    icon: 'tabler:puzzle',
  },
  {
    label: 'Profile',
    href: '/profile',
    icon: 'tabler:user-circle',
  },
  {
    label: 'Settings',
    href: '/settings',
    icon: 'tabler:settings',
  },
]

export default verticalMenuData
