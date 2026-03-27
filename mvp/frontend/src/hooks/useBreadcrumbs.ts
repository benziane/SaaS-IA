'use client';

import { usePathname } from 'next/navigation';
import { useMemo } from 'react';

const ROUTE_LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  chat: 'Chat',
  transcription: 'Transcription',
  knowledge: 'Knowledge Base',
  agents: 'AI Agents',
  pipelines: 'Pipelines',
  compare: 'Compare',
  sentiment: 'Sentiment',
  workspaces: 'Workspaces',
  billing: 'Billing',
  'api-keys': 'API Keys',
  'cost-tracker': 'Cost Tracker',
  'content-studio': 'Content Studio',
  'ai-workflows': 'AI Workflows',
  'multi-agent-crew': 'Multi-Agent Crew',
  'voice-clone': 'Voice Clone',
  'realtime-ai': 'Realtime AI',
  'security-guardian': 'Security Guardian',
  'image-gen': 'Image Gen',
  'data-analyst': 'Data Analyst',
  'video-gen': 'Video Gen',
  'ai-monitoring': 'AI Monitoring',
  'unified-search': 'Unified Search',
  'ai-memory': 'AI Memory',
  'social-publisher': 'Social Publisher',
  'integration-hub': 'Integration Hub',
  'ai-chatbot-builder': 'Chatbot Builder',
  marketplace: 'Marketplace',
  'presentation-gen': 'Presentations',
  'code-sandbox': 'Code Sandbox',
  'ai-forms': 'AI Forms',
  'skill-seekers': 'Skill Seekers',
  'repo-analyzer': 'Repo Analyzer',
  'pdf-processor': 'PDF Processor',
  'audio-studio': 'Audio Studio',
  settings: 'Settings',
  profile: 'Profile',
  tenants: 'Tenants',
  audit: 'Audit Log',
  'feature-flags': 'Feature Flags',
  secrets: 'Secrets',
  'fine-tuning': 'Fine-Tuning',
  'web-crawler': 'Web Crawler',
};

export interface BreadcrumbItem {
  label: string;
  href: string;
}

export function useBreadcrumbs(): BreadcrumbItem[] {
  const pathname = usePathname();

  return useMemo(() => {
    const segments = pathname.split('/').filter(Boolean);

    // Only on dashboard root — don't show breadcrumbs
    if (segments.length <= 1 && segments[0] === 'dashboard') {
      return [];
    }

    const crumbs: BreadcrumbItem[] = [{ label: 'Dashboard', href: '/dashboard' }];
    let accPath = '';

    for (const segment of segments) {
      accPath += `/${segment}`;
      if (segment === 'dashboard') continue;
      const label =
        ROUTE_LABELS[segment] ??
        segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' ');
      crumbs.push({ label, href: accPath });
    }

    // Single-level (just dashboard) → no crumbs
    if (crumbs.length <= 1) return [];

    return crumbs;
  }, [pathname]);
}
