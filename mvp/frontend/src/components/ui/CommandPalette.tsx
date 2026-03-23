'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Dialog,
  DialogContent,
  Divider,
  InputAdornment,
  List,
  ListItem,
  ListItemAvatar,
  ListItemButton,
  ListItemText,
  Avatar,
  TextField,
  Typography,
  Chip,
} from '@mui/material';

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
      groups[cmd.category].push(cmd);
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
    <Dialog
      open={open}
      onClose={() => setOpen(false)}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          position: 'fixed',
          top: '15%',
          m: 0,
          borderRadius: 3,
          maxHeight: '60vh',
        },
      }}
    >
      <Box sx={{ p: 2, pb: 0 }}>
        <TextField
          autoFocus
          fullWidth
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Type a command or search..."
          variant="outlined"
          size="medium"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <i className="tabler-search" style={{ fontSize: 20, opacity: 0.5 }} />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <Chip label="ESC" size="small" variant="outlined" sx={{ height: 22, fontSize: '0.7rem' }} />
              </InputAdornment>
            ),
            sx: { borderRadius: 2 },
          }}
        />
      </Box>

      <DialogContent sx={{ p: 1, pt: 1 }}>
        {filtered.length === 0 ? (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No results for &quot;{search}&quot;
            </Typography>
          </Box>
        ) : (
          Object.entries(grouped).map(([category, items]) => (
            <Box key={category}>
              <Typography
                variant="overline"
                color="text.secondary"
                sx={{ px: 2, py: 0.5, display: 'block', fontSize: '0.65rem', letterSpacing: 1.5 }}
              >
                {category}
              </Typography>
              <List disablePadding>
                {items.map((cmd) => {
                  flatIndex++;
                  const isSelected = flatIndex === selectedIndex;
                  return (
                    <ListItem key={cmd.id} disablePadding>
                      <ListItemButton
                        selected={isSelected}
                        onClick={() => handleSelect(cmd.href)}
                        sx={{
                          borderRadius: 2,
                          mx: 1,
                          mb: 0.5,
                          py: 1,
                        }}
                      >
                        <ListItemAvatar sx={{ minWidth: 40 }}>
                          <Avatar
                            sx={{
                              width: 32,
                              height: 32,
                              bgcolor: `${cmd.color}15`,
                              color: cmd.color,
                            }}
                          >
                            <i className={`tabler-${cmd.icon}`} style={{ fontSize: 16 }} />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={cmd.label}
                          secondary={cmd.description}
                          primaryTypographyProps={{ variant: 'body2', fontWeight: 600 }}
                          secondaryTypographyProps={{ variant: 'caption' }}
                        />
                      </ListItemButton>
                    </ListItem>
                  );
                })}
              </List>
            </Box>
          ))
        )}

        <Divider sx={{ mt: 1 }} />
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, py: 1 }}>
          <Typography variant="caption" color="text.secondary">
            <Chip label="↑↓" size="small" variant="outlined" sx={{ height: 18, fontSize: '0.65rem', mr: 0.5 }} />
            Navigate
          </Typography>
          <Typography variant="caption" color="text.secondary">
            <Chip label="↵" size="small" variant="outlined" sx={{ height: 18, fontSize: '0.65rem', mr: 0.5 }} />
            Open
          </Typography>
          <Typography variant="caption" color="text.secondary">
            <Chip label="Ctrl+K" size="small" variant="outlined" sx={{ height: 18, fontSize: '0.65rem', mr: 0.5 }} />
            Toggle
          </Typography>
        </Box>
      </DialogContent>
    </Dialog>
  );
}
