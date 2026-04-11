'use client';

import { useState } from 'react';
import { GitBranch, Play, Trash2, Plus, Loader2, Layers } from 'lucide-react';

import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
} from '@/lib/design-hub/components/Dialog';

import {
  useCreatePipeline,
  useDeletePipeline,
  useExecutePipeline,
  usePipelines,
} from '@/features/pipelines/hooks/usePipelines';
import type { PipelineExecution } from '@/features/pipelines/types';

const STATUS_DOT: Record<string, string> = {
  draft: 'bg-[var(--text-low)]',
  active: 'bg-[var(--success)]',
  archived: 'bg-[var(--warning)]',
};

const STEP_COLORS: Record<string, string> = {
  transcription: 'text-[var(--accent)] bg-[var(--accent)]/10',
  summarize: 'text-[#22d3ee] bg-[#22d3ee]/10',
  translate: 'text-[var(--warning)] bg-[var(--warning)]/10',
  sentiment: 'text-[var(--success)] bg-[var(--success)]/10',
};

export default function PipelinesPage() {
  const { data: pipelines, isLoading, error } = usePipelines();
  const createMutation = useCreatePipeline();
  const deleteMutation = useDeletePipeline();
  const executeMutation = useExecutePipeline();
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [execResult, setExecResult] = useState<PipelineExecution | null>(null);

  const handleCreate = () => {
    if (!newName.trim()) return;
    createMutation.mutate(
      {
        name: newName.trim(),
        description: newDesc.trim() || undefined,
        steps: [
          { id: 'step1', type: 'transcription', config: { language: 'auto' }, position: 0 },
          { id: 'step2', type: 'summarize', config: {}, position: 1 },
        ],
      },
      {
        onSuccess: () => {
          setCreateOpen(false);
          setNewName('');
          setNewDesc('');
        },
      }
    );
  };

  const handleExecute = (pipelineId: string) => {
    executeMutation.mutate(pipelineId, {
      onSuccess: (data) => setExecResult(data),
    });
  };

  if (isLoading) {
    return (
      <div className="p-5">
        <Skeleton className="w-48 h-10 mb-5" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-[200px]" />)}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-5">
        <Alert variant="destructive">
          <AlertDescription>Failed to load pipelines.</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-5 space-y-5 animate-enter">

      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#05c3db]/60 shrink-0">
            <GitBranch className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">AI Pipelines</h1>
            <p className="text-xs text-[var(--text-mid)]">Chain AI operations into automated workflows</p>
          </div>
        </div>
        <Button onClick={() => setCreateOpen(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Create Pipeline
        </Button>
      </div>

      {/* Execution Result */}
      {execResult && (
        <Alert
          variant={execResult.status === 'completed' ? 'success' : execResult.status === 'failed' ? 'destructive' : 'info'}
        >
          <AlertDescription>
            Pipeline execution {execResult.status}.
            {execResult.error && ` Error: ${execResult.error}`}
            {execResult.status === 'completed' && ` (${execResult.total_steps} steps completed)`}
          </AlertDescription>
        </Alert>
      )}

      {/* Empty State */}
      {!pipelines?.length ? (
        <div className="surface-card p-12 text-center">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--accent)]/20 mx-auto mb-4">
            <Layers className="h-7 w-7 text-[var(--accent)]" />
          </div>
          <h2 className="text-base font-semibold text-[var(--text-high)] mb-2">No pipelines yet</h2>
          <p className="text-sm text-[var(--text-mid)] max-w-sm mx-auto mb-5">
            Create your first AI pipeline to chain operations like transcription, summarization, and translation.
          </p>
          <Button onClick={() => setCreateOpen(true)} className="flex items-center gap-2 mx-auto">
            <Plus className="h-4 w-4" />
            Create Pipeline
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {pipelines.map((pipeline) => (
            <div key={pipeline.id} className="surface-card border-glow-accent flex flex-col h-full group">
              <div className="flex-1 p-5">
                {/* Card header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-[var(--bg-elevated)] shrink-0 mr-3">
                    <GitBranch className="h-4 w-4 text-[var(--accent)]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-[var(--text-high)] truncate mb-0.5">
                      {pipeline.name}
                    </h3>
                    <div className="flex items-center gap-1.5">
                      <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[pipeline.status] || 'bg-[var(--text-low)]'}`} />
                      <span className="text-xs text-[var(--text-low)] capitalize">{pipeline.status}</span>
                    </div>
                  </div>
                </div>

                {pipeline.description && (
                  <p className="text-xs text-[var(--text-mid)] mb-3 line-clamp-2">
                    {pipeline.description}
                  </p>
                )}

                {/* Step chips */}
                <div className="flex flex-wrap gap-1.5">
                  {pipeline.steps.map((step) => (
                    <span
                      key={step.id}
                      className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${STEP_COLORS[step.type] || 'text-[var(--text-low)] bg-[var(--bg-elevated)]'}`}
                    >
                      {step.type}
                    </span>
                  ))}
                </div>
              </div>

              {/* Card footer */}
              <div className="px-5 py-3 border-t border-[var(--border)] flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleExecute(pipeline.id)}
                  disabled={executeMutation.isPending}
                  className="flex items-center gap-1.5 text-xs font-medium text-[var(--accent)] hover:text-[var(--accent)]/80 disabled:opacity-50 transition-colors"
                >
                  {executeMutation.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Play className="h-3.5 w-3.5" />
                  )}
                  Execute
                </button>
                <div className="flex-1" />
                <button
                  type="button"
                  onClick={() => deleteMutation.mutate(pipeline.id)}
                  disabled={deleteMutation.isPending}
                  className="flex items-center gap-1 text-xs text-[var(--text-low)] hover:text-[var(--error)] disabled:opacity-50 transition-colors"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Pipeline Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Pipeline</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Pipeline Name</label>
              <Input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. Transcription + Summary"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Description <span className="text-[var(--text-low)] font-normal">(optional)</span></label>
              <Textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Describe what this pipeline does…"
                rows={2}
              />
            </div>
            <p className="text-xs text-[var(--text-low)] bg-[var(--bg-elevated)] rounded-lg p-3">
              A default pipeline with <strong className="text-[var(--accent)]">Transcription → Summarize</strong> steps will be created. You can edit steps later.
            </p>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCreate}
              disabled={!newName.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? 'Creating…' : 'Create Pipeline'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  );
}
