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
    href: '/transcription',
    icon: 'tabler:microphone',
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
