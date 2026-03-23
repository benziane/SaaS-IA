// Type Imports
import type { VerticalMenuDataType } from '@/types/menuTypes'

/**
 * Vertical Menu Data - SaaS-IA MVP
 * 
 * Configuration du menu vertical pour l'application SaaS-IA.
 * Utilise les icônes Iconify (Tabler Icons).
 */

const verticalMenuData = (): VerticalMenuDataType[] => [
  // Dashboard Section
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: 'tabler:smart-home',
  },
  
  // AI Modules Section
  {
    label: 'AI Modules',
    isSection: true,
  },
  {
    label: 'Transcription',
    icon: 'tabler:microphone',
    children: [
      {
        label: 'Transcription',
        href: '/transcription',
        icon: 'tabler:player-record',
      },
      {
        label: 'Debug & Test',
        href: '/transcription/debug',
        icon: 'tabler:bug',
      },
    ],
  },
  {
    label: 'Chat IA',
    href: '/chat',
    icon: 'tabler:message-chatbot',
  },
  {
    label: 'Compare',
    href: '/compare',
    icon: 'tabler:arrows-diff',
  },
  {
    label: 'Pipelines',
    href: '/pipelines',
    icon: 'tabler:git-branch',
  },
  {
    label: 'Knowledge Base',
    href: '/knowledge',
    icon: 'tabler:books',
  },
  {
    label: 'AI Agents',
    href: '/agents',
    icon: 'tabler:robot',
  },
  {
    label: 'Sentiment',
    href: '/sentiment',
    icon: 'tabler:mood-happy',
  },
  {
    label: 'Web Crawler',
    href: '/crawler',
    icon: 'tabler:world-download',
  },

  // Platform Section
  {
    label: 'Platform',
    isSection: true,
  },
  {
    label: 'Modules',
    href: '/modules',
    icon: 'tabler:puzzle',
  },
  {
    label: 'API & Keys',
    href: '/api-docs',
    icon: 'tabler:key',
  },
  {
    label: 'Workspaces',
    href: '/workspaces',
    icon: 'tabler:users-group',
  },
  {
    label: 'Cost Tracker',
    href: '/costs',
    icon: 'tabler:chart-dots',
  },

  // Account Section
  {
    label: 'Account',
    isSection: true,
  },
  {
    label: 'Profile',
    href: '/profile',
    icon: 'tabler:user-circle',
  },
  {
    label: 'Billing',
    href: '/billing',
    icon: 'tabler:credit-card',
  },

  // Future Modules (commented for now)
  // {
  //   label: 'Text Generation',
  //   href: '/text-generation',
  //   icon: 'tabler:file-text',
  // },
  // {
  //   label: 'Image Analysis',
  //   href: '/image-analysis',
  //   icon: 'tabler:photo',
  // },
]

export default verticalMenuData
