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
