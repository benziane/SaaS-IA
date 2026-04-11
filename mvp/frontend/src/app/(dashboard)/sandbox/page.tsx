'use client';

import { useState } from 'react';
import {
  Code, Plus, Play, Trash2, Wand2, Bug, Lightbulb, Bot, Loader2, Terminal,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/lib/design-hub/components/Dialog';

import {
  useAddCell, useCreateSandbox, useDeleteCell, useDeleteSandbox,
  useExecuteCell, useExplainCode, useGenerateCode, useDebugCode,
  useSandbox, useSandboxes, useUpdateCell,
} from '@/features/code-sandbox/hooks/useCodeSandbox';
import type { SandboxCell } from '@/features/code-sandbox/types';

const STATUS_VARIANTS: Record<string, 'default' | 'secondary' | 'success' | 'destructive' | 'warning'> = {
  idle: 'default', running: 'secondary', success: 'success', error: 'destructive', timeout: 'warning',
  active: 'success', archived: 'default',
};

export default function SandboxPage() {
  const { data: sandboxes, isLoading } = useSandboxes();
  const createMutation = useCreateSandbox();
  const deleteSandboxMutation = useDeleteSandbox();

  const [activeSandboxId, setActiveSandboxId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [generatePrompt, setGeneratePrompt] = useState('');

  const { data: activeSandbox } = useSandbox(activeSandboxId);
  const addCellMutation = useAddCell(activeSandboxId || '');
  const executeCellMutation = useExecuteCell(activeSandboxId || '');
  const deleteCellMutation = useDeleteCell(activeSandboxId || '');
  const updateCellMutation = useUpdateCell(activeSandboxId || '');
  const generateMutation = useGenerateCode();
  const explainMutation = useExplainCode();
  const debugMutation = useDebugCode();

  const [editingSources, setEditingSources] = useState<Record<string, string>>({});

  const handleCreate = () => {
    if (!newName.trim()) return;
    createMutation.mutate(
      { name: newName, description: newDesc || undefined },
      { onSuccess: (s) => { setActiveSandboxId(s.id); setCreateOpen(false); setNewName(''); setNewDesc(''); } },
    );
  };

  const handleAddCell = () => {
    addCellMutation.mutate({ source: '# Write your code here\n', cell_type: 'code' });
  };

  const handleExecute = (cellId: string) => {
    const pendingSource = editingSources[cellId];
    if (pendingSource !== undefined) {
      updateCellMutation.mutate(
        { cellId, source: pendingSource },
        { onSuccess: () => { executeCellMutation.mutate(cellId); } },
      );
    } else {
      executeCellMutation.mutate(cellId);
    }
  };

  const handleGenerate = () => {
    if (!generatePrompt.trim()) return;
    generateMutation.mutate(
      { prompt: generatePrompt },
      {
        onSuccess: (res) => {
          addCellMutation.mutate({ source: res.code, cell_type: 'code' });
          setGeneratePrompt('');
        },
      },
    );
  };

  const handleExplain = (code: string) => {
    explainMutation.mutate(code);
  };

  const handleDebug = (cell: SandboxCell) => {
    if (cell.error) {
      debugMutation.mutate(
        { code: cell.source, error: cell.error },
        {
          onSuccess: (res) => {
            addCellMutation.mutate({ source: res.fixed_code, cell_type: 'code' });
          },
        },
      );
    }
  };

  const getCellSource = (cell: SandboxCell) => editingSources[cell.id] ?? cell.source;

  return (
    <div className="p-5 space-y-5 animate-enter">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
          <Terminal className="h-5 w-5 text-[var(--accent)]" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Code Sandbox</h1>
          <p className="text-xs text-[var(--text-mid)]">Secure AI code execution environment</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
        {/* Sandbox list */}
        <div className="md:col-span-3">
          <div className="surface-card p-5">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-[var(--text-high)]">Sandboxes</h3>
              <Button size="sm" variant="outline" onClick={() => setCreateOpen(true)}>
                <Plus className="h-3.5 w-3.5 mr-1" /> New
              </Button>
            </div>

            {isLoading ? <Skeleton className="h-52 rounded-lg" /> : !sandboxes?.length ? (
              <div className="text-center py-8">
                <Code className="h-12 w-12 text-[var(--text-low)] mx-auto mb-2" />
                <p className="text-[var(--text-mid)]">Create your first sandbox</p>
              </div>
            ) : (
              sandboxes.map((s) => (
                <div
                  key={s.id}
                  className={`surface-card mb-2 cursor-pointer border border-[var(--border)] transition-colors hover:bg-[var(--bg-hover)] p-3 ${
                    activeSandboxId === s.id ? 'bg-[var(--bg-surface)]' : ''
                  }`}
                  onClick={() => { setActiveSandboxId(s.id); setEditingSources({}); }}
                >
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-[var(--text-high)] truncate">{s.name}</span>
                    <button
                      type="button"
                      title="Delete"
                      className="p-1 rounded hover:bg-red-100 text-red-500"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSandboxMutation.mutate(s.id);
                        if (activeSandboxId === s.id) setActiveSandboxId(null);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="flex gap-1 mt-1">
                    <Badge variant="outline">{s.language}</Badge>
                    <Badge variant="outline">{s.cells.length} cells</Badge>
                    <Badge variant={STATUS_VARIANTS[s.status] || 'default'}>{s.status}</Badge>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Editor & output */}
        <div className="md:col-span-9">
          {activeSandbox ? (
            <div className="space-y-4">
              {/* AI generate bar */}
              <div className="surface-card p-4">
                <div className="flex gap-2 items-center">
                  <Bot className="h-5 w-5 text-[var(--accent)] shrink-0" />
                  <Input
                    placeholder="Describe what code you want to generate..."
                    value={generatePrompt}
                    onChange={(e) => setGeneratePrompt(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleGenerate(); }}
                  />
                  <Button
                    size="sm"
                    onClick={handleGenerate}
                    disabled={!generatePrompt.trim() || generateMutation.isPending}
                  >
                    {generateMutation.isPending ? (
                      <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
                    ) : (
                      <Wand2 className="h-3.5 w-3.5 mr-1" />
                    )}
                    Generate
                  </Button>
                </div>
              </div>

              {/* Cells */}
              {activeSandbox.cells.map((cell, idx) => (
                <div key={cell.id} className="surface-card p-4">
                  <div className="flex justify-between items-center mb-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[var(--accent)]">[{idx + 1}]</Badge>
                      <Badge variant="outline">{cell.language}</Badge>
                      {cell.status !== 'idle' && (
                        <Badge variant={STATUS_VARIANTS[cell.status] || 'default'}>{cell.status}</Badge>
                      )}
                      {cell.execution_time_ms != null && (
                        <span className="text-xs text-[var(--text-mid)]">
                          {cell.execution_time_ms.toFixed(0)}ms
                        </span>
                      )}
                    </div>
                    <div className="flex gap-1">
                      <button
                        type="button"
                        title="Run cell"
                        className="p-1 rounded hover:bg-green-100 text-green-600"
                        onClick={() => handleExecute(cell.id)}
                        disabled={executeCellMutation.isPending}
                      >
                        {executeCellMutation.isPending && executeCellMutation.variables === cell.id
                          ? <Loader2 className="h-4 w-4 animate-spin" />
                          : <Play className="h-4 w-4" />}
                      </button>
                      <button
                        type="button"
                        title="Explain code"
                        className="p-1 rounded hover:bg-[var(--bg-hover)]"
                        onClick={() => handleExplain(getCellSource(cell))}
                        disabled={explainMutation.isPending}
                      >
                        <Lightbulb className="h-4 w-4 text-[var(--text-mid)]" />
                      </button>
                      {cell.error && (
                        <button
                          type="button"
                          title="Debug with AI"
                          className="p-1 rounded hover:bg-yellow-100 text-yellow-600"
                          onClick={() => handleDebug(cell)}
                          disabled={debugMutation.isPending}
                        >
                          <Bug className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        type="button"
                        title="Delete cell"
                        className="p-1 rounded hover:bg-red-100 text-red-500"
                        onClick={() => deleteCellMutation.mutate(cell.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {/* Code editor */}
                  <Textarea
                    className="font-mono text-sm bg-gray-50 dark:bg-gray-900"
                    rows={4}
                    value={getCellSource(cell)}
                    onChange={(e) => setEditingSources((prev) => ({ ...prev, [cell.id]: e.target.value }))}
                    onBlur={() => {
                      const src = editingSources[cell.id];
                      if (src !== undefined && src !== cell.source) {
                        updateCellMutation.mutate({ cellId: cell.id, source: src });
                      }
                    }}
                  />

                  {/* Output */}
                  {cell.output && (
                    <div className="mt-2 p-3 bg-gray-900 rounded max-h-72 overflow-auto">
                      <pre className="font-mono text-[0.8rem] text-green-400 whitespace-pre-wrap m-0">
                        {cell.output}
                      </pre>
                    </div>
                  )}

                  {/* Error */}
                  {cell.error && (
                    <Alert variant="destructive" className="mt-2 font-mono text-[0.8rem]">
                      <AlertDescription>{cell.error}</AlertDescription>
                    </Alert>
                  )}
                </div>
              ))}

              {/* Add cell button */}
              <div className="text-center py-4">
                <Button variant="outline" onClick={handleAddCell}>
                  <Plus className="h-4 w-4 mr-2" /> Add Cell
                </Button>
              </div>

              {/* AI explanation panel */}
              {explainMutation.data && (
                <div className="surface-card p-4">
                  <p className="text-sm font-medium text-[var(--accent)] mb-2 flex items-center gap-1">
                    <Lightbulb className="h-4 w-4" /> AI Explanation
                  </p>
                  <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap">
                    {explainMutation.data.explanation}
                  </p>
                  {explainMutation.data.complexity && (
                    <Badge className="mt-2">Complexity: {explainMutation.data.complexity}</Badge>
                  )}
                </div>
              )}

              {/* Debug result panel */}
              {debugMutation.data && (
                <div className="surface-card p-4">
                  <p className="text-sm font-medium text-yellow-600 mb-2 flex items-center gap-1">
                    <Bug className="h-4 w-4" /> Debug Result
                  </p>
                  <Alert className="mb-2">
                    <AlertDescription>Root cause: {debugMutation.data.root_cause}</AlertDescription>
                  </Alert>
                  <p className="text-sm text-[var(--text-high)] whitespace-pre-wrap">
                    {debugMutation.data.explanation}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="surface-card p-5 text-center py-16">
              <Code className="h-16 w-16 text-[var(--text-low)] mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-[var(--text-mid)]">Select or create a sandbox to start coding</h3>
              <p className="text-sm text-[var(--text-mid)]">
                Write code, run it in a secure environment, and use AI to generate, explain, or debug
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Create dialog */}
      <Dialog open={createOpen} onOpenChange={(v) => { if (!v) setCreateOpen(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create New Sandbox</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <Input
              placeholder="Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
            />
            <Textarea
              placeholder="Description (optional)"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              rows={2}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={!newName.trim() || createMutation.isPending}>
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
