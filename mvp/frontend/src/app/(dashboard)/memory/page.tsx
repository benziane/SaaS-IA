'use client';

import { useEffect, useState } from 'react';
import { Brain, Plus, Trash2, Sparkles, Loader2 } from 'lucide-react';

import { Badge } from '@/lib/design-hub/components/Badge';
import { Button } from '@/lib/design-hub/components/Button';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/lib/design-hub/components/Dialog';

import apiClient from '@/lib/apiClient';

interface Memory {
  id: string; memory_type: string; content: string; category: string | null;
  confidence: number; source: string; active: boolean; use_count: number;
  created_at: string;
}

const TYPE_ICONS: Record<string, string> = {
  preference: '\u2B50', fact: '\uD83D\uDCCC', context: '\uD83C\uDFAF', instruction: '\uD83D\uDCCB',
};
const TYPE_VARIANT: Record<string, 'default' | 'success' | 'secondary' | 'warning'> = {
  preference: 'default', fact: 'success', context: 'secondary', instruction: 'warning',
};

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [context, setContext] = useState('');
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [extractOpen, setExtractOpen] = useState(false);
  const [newContent, setNewContent] = useState('');
  const [newType, setNewType] = useState('fact');
  const [extractText, setExtractText] = useState('');
  const [extracting, setExtracting] = useState(false);

  const fetchData = async () => {
    try {
      const [memResp, ctxResp] = await Promise.all([
        apiClient.get('/api/memory/'),
        apiClient.get('/api/memory/context'),
      ]);
      setMemories(memResp.data || []);
      setContext(ctxResp.data?.context || '');
    } catch {}
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleAdd = async () => {
    if (!newContent.trim()) return;
    await apiClient.post('/api/memory/', { content: newContent, memory_type: newType });
    setAddOpen(false); setNewContent('');
    fetchData();
  };

  const handleDelete = async (id: string) => {
    await apiClient.delete(`/api/memory/${id}`);
    fetchData();
  };

  const handleExtract = async () => {
    if (!extractText.trim()) return;
    setExtracting(true);
    try {
      await apiClient.post('/api/memory/extract', { text: extractText, source: 'manual' });
      setExtractOpen(false); setExtractText('');
      fetchData();
    } catch {}
    setExtracting(false);
  };

  const handleForgetAll = async () => {
    if (!confirm('Are you sure? This will deactivate ALL memories (RGPD).')) return;
    await apiClient.delete('/api/memory/forget-all');
    fetchData();
  };

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
            <Brain className="h-5 w-5 text-[var(--accent)]" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">AI Memory</h1>
            <p className="text-xs text-[var(--text-mid)]">Your AI remembers preferences, facts, and context to personalize all responses</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setExtractOpen(true)}>
            <Sparkles className="h-4 w-4 mr-1" />
            Auto-Extract
          </Button>
          <Button onClick={() => setAddOpen(true)}>
            <Plus className="h-4 w-4 mr-1" />
            Add Memory
          </Button>
        </div>
      </div>

      {/* Context Preview */}
      {context && (
        <div className="surface-card p-5 bg-[var(--bg-elevated)]">
          <h4 className="text-sm font-semibold mb-2">Context Injected into AI Prompts</h4>
          <p className="text-sm whitespace-pre-wrap font-mono text-[0.85rem]">
            {context}
          </p>
        </div>
      )}

      {/* Memories */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full flex justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-[var(--accent)]" />
          </div>
        ) : memories.length === 0 ? (
          <div className="col-span-full">
            <div className="surface-card p-5 text-center py-12">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] mx-auto mb-4">
                <Brain className="h-8 w-8 text-white" />
              </div>
              <p className="text-[var(--text-mid)]">No memories yet. Add one or auto-extract from text.</p>
            </div>
          </div>
        ) : (
          memories.map((mem) => (
            <div key={mem.id} className="surface-card p-4">
              <div className="flex justify-between mb-2">
                <Badge variant={TYPE_VARIANT[mem.memory_type] || 'secondary'}>
                  {TYPE_ICONS[mem.memory_type] || '\uD83D\uDCCC'} {mem.memory_type}
                </Badge>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-red-500 hover:text-red-600"
                  onClick={() => handleDelete(mem.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-sm mb-2">{mem.content}</p>
              <div className="flex gap-1 flex-wrap">
                {mem.category && <Badge variant="outline">{mem.category}</Badge>}
                <Badge variant="outline">{(mem.confidence * 100).toFixed(0)}%</Badge>
                <Badge variant="outline">used {mem.use_count}x</Badge>
                <Badge variant="outline">{mem.source}</Badge>
              </div>
            </div>
          ))
        )}
      </div>

      {memories.length > 0 && (
        <div className="mt-6 text-center">
          <Button variant="destructive" onClick={handleForgetAll}>
            <Trash2 className="h-4 w-4 mr-1" />
            Forget All (RGPD)
          </Button>
        </div>
      )}

      {/* Add Memory Dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Memory</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <div>
              <label className="block text-sm font-medium mb-1 text-[var(--text-mid)]">Memory content</label>
              <Textarea
                placeholder="e.g., I prefer formal tone..."
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                rows={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-[var(--text-mid)]">Type</label>
              <Select value={newType} onValueChange={setNewType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="preference">Preference</SelectItem>
                  <SelectItem value="fact">Fact</SelectItem>
                  <SelectItem value="context">Context</SelectItem>
                  <SelectItem value="instruction">Instruction</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="ghost" onClick={() => setAddOpen(false)}>Cancel</Button>
            <Button onClick={handleAdd} disabled={!newContent.trim()}>Add</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Extract Dialog */}
      <Dialog open={extractOpen} onOpenChange={setExtractOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Auto-Extract Memories from Text</DialogTitle>
          </DialogHeader>
          <div className="mt-2">
            <label className="block text-sm font-medium mb-1 text-[var(--text-mid)]">Paste any text</label>
            <Textarea
              rows={6}
              placeholder="Paste a conversation, notes, or any text. AI will extract preferences, facts, and instructions..."
              value={extractText}
              onChange={(e) => setExtractText(e.target.value)}
            />
          </div>
          <DialogFooter className="mt-4">
            <Button variant="ghost" onClick={() => setExtractOpen(false)}>Cancel</Button>
            <Button
              onClick={handleExtract}
              disabled={!extractText.trim() || extracting}
            >
              {extracting
                ? <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                : <Sparkles className="h-4 w-4 mr-1" />}
              Extract
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
