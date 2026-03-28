'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/lib/design-hub/components/Input';
import { Separator } from '@/lib/design-hub/components/Separator';
import { Avatar, AvatarFallback } from '@/lib/design-hub/components/Avatar';
import {
  Dialog,
  DialogContent,
} from '@/lib/design-hub/components/Dialog';

interface CommandItem {
  id: string;
  label: string;
  description: string;
  href: string;
  icon: string;
  color: string;
  category: string;
  keywords: string[];
}

const COMMANDS: CommandItem[] = [
  // Navigation
  { id: 'dashboard', label: 'Dashboard', description: 'Overview and stats', href: '/dashboard', icon: 'smart-home', color: '#667eea', category: 'Navigation', keywords: ['home', 'overview', 'stats'] },
  { id: 'transcription', label: 'Transcription', description: 'Transcribe audio and video', href: '/transcription', icon: 'microphone', color: '#7367f0', category: 'AI Modules', keywords: ['youtube', 'audio', 'video', 'upload', 'record'] },
  { id: 'chat', label: 'Chat IA', description: 'AI chat with context', href: '/chat', icon: 'message-chatbot', color: '#28c76f', category: 'AI Modules', keywords: ['conversation', 'ask', 'question', 'assistant'] },
  { id: 'compare', label: 'Compare Models', description: 'Compare AI providers', href: '/compare', icon: 'arrows-diff', color: '#ff9f43', category: 'AI Modules', keywords: ['gemini', 'claude', 'groq', 'benchmark'] },
  { id: 'pipelines', label: 'Pipelines', description: 'AI workflow builder', href: '/pipelines', icon: 'git-branch', color: '#ea5455', category: 'AI Modules', keywords: ['workflow', 'chain', 'automate', 'builder'] },
  { id: 'knowledge', label: 'Knowledge Base', description: 'Documents and RAG search', href: '/knowledge', icon: 'books', color: '#00cfe8', category: 'AI Modules', keywords: ['document', 'pdf', 'rag', 'search', 'upload'] },
  { id: 'agents', label: 'AI Agents', description: 'Autonomous task execution', href: '/agents', icon: 'robot', color: '#ff6b6b', category: 'AI Modules', keywords: ['autonomous', 'task', 'execute', 'agent'] },
  { id: 'sentiment', label: 'Sentiment Analysis', description: 'Analyze emotions in text', href: '/sentiment', icon: 'mood-happy', color: '#ffd93d', category: 'AI Modules', keywords: ['emotion', 'tone', 'positive', 'negative'] },
  { id: 'crawler', label: 'Web Crawler', description: 'Scrape and index websites', href: '/crawler', icon: 'world-download', color: '#764ba2', category: 'AI Modules', keywords: ['scrape', 'website', 'crawl', 'index', 'images'] },
  { id: 'costs', label: 'Cost Tracker', description: 'AI usage costs and analytics', href: '/costs', icon: 'chart-dots', color: '#20c997', category: 'Platform', keywords: ['cost', 'money', 'usage', 'price', 'analytics'] },
  { id: 'modules', label: 'Modules', description: 'Platform module registry', href: '/modules', icon: 'puzzle', color: '#868e96', category: 'Platform', keywords: ['module', 'plugin', 'registry'] },
  { id: 'api-docs', label: 'API & Keys', description: 'API keys and documentation', href: '/api-docs', icon: 'key', color: '#339af0', category: 'Platform', keywords: ['api', 'key', 'developer', 'documentation'] },
  { id: 'workspaces', label: 'Workspaces', description: 'Team collaboration', href: '/workspaces', icon: 'users-group', color: '#845ef7', category: 'Platform', keywords: ['team', 'workspace', 'collaboration', 'share'] },
  { id: 'profile', label: 'Profile', description: 'Account settings', href: '/profile', icon: 'user-circle', color: '#495057', category: 'Account', keywords: ['account', 'settings', 'password', 'name'] },
  { id: 'billing', label: 'Billing', description: 'Plans and subscription', href: '/billing', icon: 'credit-card', color: '#fab005', category: 'Account', keywords: ['plan', 'subscription', 'upgrade', 'pro', 'payment'] },
  // Content & Media
  { id: 'content-studio', label: 'Content Studio', description: '10 content formats with AI', href: '/content-studio', icon: 'sparkles', color: '#f43f5e', category: 'Content & Media', keywords: ['blog', 'tweet', 'linkedin', 'email', 'content', 'generate'] },
  { id: 'images', label: 'Image Generation', description: 'AI image generation, 10 styles', href: '/images', icon: 'photo-ai', color: '#8b5cf6', category: 'Content & Media', keywords: ['image', 'art', 'generate', 'dalle', 'stable diffusion'] },
  { id: 'video-studio', label: 'Video Studio', description: 'AI video generation', href: '/video-studio', icon: 'video', color: '#06b6d4', category: 'Content & Media', keywords: ['video', 'generate', 'clip', 'animation'] },
  { id: 'voice', label: 'Voice Clone', description: 'TTS and voice cloning', href: '/voice', icon: 'microphone-2', color: '#f97316', category: 'Content & Media', keywords: ['voice', 'tts', 'clone', 'speech', 'audio'] },
  { id: 'presentations', label: 'Presentations', description: 'AI slide deck generator', href: '/presentations', icon: 'presentation', color: '#14b8a6', category: 'Content & Media', keywords: ['slides', 'powerpoint', 'presentation', 'deck'] },
  { id: 'audio-studio', label: 'Audio Studio', description: 'Audio editing and processing', href: '/audio-studio', icon: 'waveform', color: '#a855f7', category: 'Content & Media', keywords: ['audio', 'edit', 'noise', 'podcast'] },
  { id: 'social', label: 'Social Publisher', description: 'Multi-platform social publishing', href: '/social', icon: 'share', color: '#3b82f6', category: 'Content & Media', keywords: ['social', 'twitter', 'instagram', 'publish', 'schedule'] },
  { id: 'batch-crawl', label: 'Batch Crawl', description: 'Crawl multiple URLs in parallel with proxy rotation', href: '/web-crawler?tab=batch', icon: 'globe', color: '#764ba2', category: 'Content & Media', keywords: ['crawl', 'batch', 'parallel', 'proxy', 'scrape', 'urls'] },
  { id: 'deep-crawl', label: 'Deep Crawl', description: 'Spider a full site with BestFirst strategy', href: '/web-crawler?tab=deep', icon: 'globe', color: '#764ba2', category: 'Content & Media', keywords: ['crawl', 'deep', 'spider', 'site', 'bestfirst', 'scrape'] },
  // Intelligence
  { id: 'crews', label: 'Multi-Agent Crews', description: '9 roles, autonomous multi-agent teams', href: '/crews', icon: 'users', color: '#6366f1', category: 'Intelligence', keywords: ['crew', 'multi', 'agent', 'team', 'autonomous'] },
  { id: 'memory', label: 'AI Memory', description: 'Persistent memory and context', href: '/memory', icon: 'brain', color: '#8b5cf6', category: 'Intelligence', keywords: ['memory', 'context', 'remember', 'persist'] },
  { id: 'realtime', label: 'Realtime AI', description: 'Voice, vision and meeting AI', href: '/realtime', icon: 'radio', color: '#ec4899', category: 'Intelligence', keywords: ['realtime', 'live', 'voice', 'meeting', 'vision'] },
  { id: 'data', label: 'Data Analyst', description: 'DuckDB + natural language queries', href: '/data', icon: 'chart-bar', color: '#0ea5e9', category: 'Intelligence', keywords: ['data', 'analyst', 'sql', 'query', 'csv', 'excel'] },
  { id: 'fine-tuning', label: 'Fine-Tuning', description: 'Custom model training with LoRA', href: '/fine-tuning', icon: 'adjustments', color: '#f59e0b', category: 'Intelligence', keywords: ['fine-tune', 'train', 'lora', 'dataset', 'model'] },
  // Security & Compliance
  { id: 'security', label: 'Security Guardian', description: 'PII detection and injection scan', href: '/security', icon: 'shield', color: '#ef4444', category: 'Security', keywords: ['security', 'pii', 'scan', 'injection', 'compliance'] },
  { id: 'tenants', label: 'Tenants', description: 'Multi-tenant isolation', href: '/tenants', icon: 'building', color: '#6b7280', category: 'Security', keywords: ['tenant', 'organization', 'isolation', 'rls'] },
  { id: 'feature-flags', label: 'Feature Flags', description: 'Kill switches and % rollouts', href: '/feature-flags', icon: 'flag', color: '#10b981', category: 'Security', keywords: ['feature', 'flag', 'rollout', 'kill', 'switch'] },
  { id: 'secrets', label: 'Secrets Manager', description: 'API keys rotation and health score', href: '/secrets', icon: 'lock', color: '#f59e0b', category: 'Security', keywords: ['secret', 'key', 'rotation', 'vault'] },
  // Platform & Dev
  { id: 'monitoring', label: 'AI Monitoring', description: 'LLM observability and traces', href: '/monitoring', icon: 'activity', color: '#06b6d4', category: 'Platform', keywords: ['monitor', 'observability', 'latency', 'trace', 'cost'] },
  { id: 'search', label: 'Unified Search', description: 'Cross-module RAG search', href: '/search', icon: 'search', color: '#8b5cf6', category: 'Platform', keywords: ['search', 'rag', 'unified', 'cross', 'module'] },
  { id: 'sandbox', label: 'Code Sandbox', description: 'Secure AI code execution', href: '/sandbox', icon: 'terminal-2', color: '#1d4ed8', category: 'Platform', keywords: ['code', 'execute', 'sandbox', 'python', 'js'] },
  { id: 'pdf', label: 'PDF Processor', description: 'Extract text and tables from PDFs', href: '/pdf', icon: 'file-type-pdf', color: '#dc2626', category: 'Platform', keywords: ['pdf', 'extract', 'table', 'document'] },
  { id: 'repo-analyzer', label: 'Repo Analyzer', description: 'Git repo code metrics', href: '/repo-analyzer', icon: 'git-merge', color: '#7c3aed', category: 'Platform', keywords: ['repo', 'git', 'code', 'metrics', 'analyze'] },
  { id: 'integrations', label: 'Integration Hub', description: '10 connectors, webhooks, triggers', href: '/integrations', icon: 'plug', color: '#0891b2', category: 'Platform', keywords: ['integration', 'webhook', 'connector', 'zapier', 'slack'] },
  { id: 'chatbots', label: 'Chatbot Builder', description: 'RAG chatbots, embed widget', href: '/chatbots', icon: 'robot', color: '#059669', category: 'Platform', keywords: ['chatbot', 'widget', 'embed', 'rag', 'channel'] },
  { id: 'marketplace', label: 'Marketplace', description: 'Module marketplace, 8 categories', href: '/marketplace', icon: 'shopping-cart', color: '#d97706', category: 'Platform', keywords: ['marketplace', 'install', 'module', 'plugin', 'store'] },
  { id: 'forms', label: 'AI Forms', description: 'Conversational forms with AI', href: '/forms', icon: 'forms', color: '#7c3aed', category: 'Platform', keywords: ['form', 'survey', 'conversational', 'ai'] },
  { id: 'workflows', label: 'Workflows', description: 'DAG workflow engine', href: '/workflows', icon: 'git-branch', color: '#0f172a', category: 'Platform', keywords: ['workflow', 'dag', 'automation', 'trigger'] },
  { id: 'pipeline-builder', label: 'Pipeline Builder', description: 'Visual drag-and-drop pipeline', href: '/pipeline-builder', icon: 'layout-kanban', color: '#be185d', category: 'Platform', keywords: ['pipeline', 'visual', 'builder', 'drag', 'drop'] },
  { id: 'youtube', label: 'YouTube Studio', description: 'YouTube transcription and analysis', href: '/youtube', icon: 'brand-youtube', color: '#ef4444', category: 'AI Modules', keywords: ['youtube', 'video', 'subtitle', 'playlist', 'live'] },
  { id: 'settings', label: 'Settings', description: 'Appearance, language, account', href: '/settings', icon: 'settings', color: '#6b7280', category: 'Account', keywords: ['settings', 'theme', 'dark', 'light', 'language'] },
];

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const router = useRouter();

  // Keyboard shortcut: Ctrl+K or Cmd+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((prev) => !prev);
        setSearch('');
        setSelectedIndex(0);
      }
      if (e.key === 'Escape') {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Filter commands
  const filtered = useMemo(() => {
    if (!search.trim()) return COMMANDS;
    const q = search.toLowerCase();
    return COMMANDS.filter(
      (cmd) =>
        cmd.label.toLowerCase().includes(q) ||
        cmd.description.toLowerCase().includes(q) ||
        cmd.keywords.some((k) => k.includes(q)) ||
        cmd.category.toLowerCase().includes(q)
    );
  }, [search]);

  // Group by category
  const grouped = useMemo(() => {
    const groups: Record<string, CommandItem[]> = {};
    for (const cmd of filtered) {
      if (!groups[cmd.category]) groups[cmd.category] = [];
      groups[cmd.category]!.push(cmd);
    }
    return groups;
  }, [filtered]);

  // Navigate on selection
  const handleSelect = useCallback(
    (href: string) => {
      setOpen(false);
      setSearch('');
      router.push(href);
    },
    [router]
  );

  // Keyboard navigation
  useEffect(() => {
    if (!open) return;

    const handleNav = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, filtered.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter' && filtered[selectedIndex]) {
        e.preventDefault();
        handleSelect(filtered[selectedIndex].href);
      }
    };
    window.addEventListener('keydown', handleNav);
    return () => window.removeEventListener('keydown', handleNav);
  }, [open, filtered, selectedIndex, handleSelect]);

  // Reset index when search changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  let flatIndex = -1;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="fixed top-[15%] translate-y-0 max-w-lg max-h-[60vh] p-0 gap-0 overflow-hidden">
        <div className="p-4 pb-0">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 opacity-50 text-[var(--text-low)]" />
            <Input
              autoFocus
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Type a command or search..."
              className="pl-10 pr-16"
            />
            <Badge variant="outline" className="absolute right-3 top-1/2 -translate-y-1/2 h-[22px] text-[0.7rem]">
              ESC
            </Badge>
          </div>
        </div>

        <div className="p-2 pt-2 overflow-auto max-h-[calc(60vh-120px)]">
          {filtered.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-sm text-[var(--text-low)]">
                No results for &quot;{search}&quot;
              </p>
            </div>
          ) : (
            Object.entries(grouped).map(([category, items]) => (
              <div key={category}>
                <span className="px-4 py-1 block text-[0.65rem] uppercase tracking-[1.5px] text-[var(--text-low)] font-medium">
                  {category}
                </span>
                <ul>
                  {items.map((cmd) => {
                    flatIndex++;
                    const isSelected = flatIndex === selectedIndex;
                    return (
                      <li key={cmd.id}>
                        <button
                          onClick={() => handleSelect(cmd.href)}
                          className={`w-full flex items-center gap-3 rounded-lg mx-1 mb-0.5 py-2 px-3 text-left transition-colors ${
                            isSelected
                              ? 'bg-[var(--bg-elevated)] text-[var(--text-high)]'
                              : 'hover:bg-[var(--bg-elevated)]/50 text-[var(--text-mid)]'
                          }`}
                        >
                          <Avatar className="h-8 w-8">
                            <AvatarFallback
                              className="text-xs"
                              style={{ backgroundColor: `${cmd.color}15`, color: cmd.color }}
                            >
                              <i className={`tabler-${cmd.icon}`} style={{ fontSize: 16 }} />
                            </AvatarFallback>
                          </Avatar>
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-semibold truncate">{cmd.label}</p>
                            <p className="text-xs text-[var(--text-low)] truncate">{cmd.description}</p>
                          </div>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))
          )}

          <Separator className="mt-2" />
          <div className="flex justify-center gap-4 py-2">
            <span className="text-xs text-[var(--text-low)] flex items-center gap-1">
              <Badge variant="outline" className="h-[18px] text-[0.65rem]">&#8593;&#8595;</Badge>
              Navigate
            </span>
            <span className="text-xs text-[var(--text-low)] flex items-center gap-1">
              <Badge variant="outline" className="h-[18px] text-[0.65rem]">&#8629;</Badge>
              Open
            </span>
            <span className="text-xs text-[var(--text-low)] flex items-center gap-1">
              <Badge variant="outline" className="h-[18px] text-[0.65rem]">Ctrl+K</Badge>
              Toggle
            </span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
