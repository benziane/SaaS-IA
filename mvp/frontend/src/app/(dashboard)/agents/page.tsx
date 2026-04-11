'use client';

import { useState } from 'react';
import { Bot, Zap, ChevronRight, History } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Spinner } from '@/components/ui/spinner';
import { Button } from '@/lib/design-hub/components/Button';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/lib/design-hub/components/Dialog';

import { useAgentRuns, useRunAgent } from '@/features/agents/hooks/useAgents';
import type { AgentRun, AgentStep } from '@/features/agents/types';

const STATUS_VARIANTS: Record<string, 'secondary' | 'default' | 'success' | 'destructive' | 'warning'> = {
  planning: 'secondary',
  executing: 'default',
  completed: 'success',
  failed: 'destructive',
  cancelled: 'warning',
};

const STATUS_COLORS: Record<string, string> = {
  planning: 'bg-[var(--text-low)]',
  executing: 'bg-[var(--accent)] animate-pulse',
  completed: 'bg-[var(--success)]',
  failed: 'bg-[var(--error)]',
  cancelled: 'bg-[var(--warning)]',
};

const ACTION_LABELS: Record<string, string> = {
  transcribe: 'Transcription',
  summarize: 'Summarization',
  translate: 'Translation',
  search_knowledge: 'Knowledge Search',
  ask_knowledge: 'RAG Query',
  compare_models: 'Model Comparison',
  generate_text: 'Text Generation',
  extract_info: 'Info Extraction',
  analyze_sentiment: 'Sentiment Analysis',
  create_pipeline: 'Pipeline Creation',
};

const SUGGESTIONS = [
  'Summarize my latest transcription',
  'Search knowledge base for meeting notes',
  'Analyze sentiment of customer feedback',
  'Compare AI models on: explain quantum computing',
];

function StepOutputDialog({ step, open, onClose }: { step: AgentStep | null; open: boolean; onClose: () => void }) {
  if (!step) return null;
  let output = '';
  if (step.output_json) {
    try {
      const parsed = typeof step.output_json === 'string' ? JSON.parse(step.output_json) : step.output_json;
      output = parsed?.output || JSON.stringify(parsed, null, 2);
    } catch {
      output = step.output_json;
    }
  }
  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{ACTION_LABELS[step.action] || step.action}</DialogTitle>
          <DialogDescription>{step.description}</DialogDescription>
        </DialogHeader>
        <div className="max-h-[70vh] overflow-y-auto border-t border-[var(--border)] pt-4">
          <p className="whitespace-pre-wrap break-words font-mono text-sm text-[var(--text-high)]">
            {output || 'No output available.'}
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function RunCard({ run }: { run: AgentRun }) {
  const [selectedStep, setSelectedStep] = useState<AgentStep | null>(null);
  const progress = run.total_steps > 0 ? (run.current_step / run.total_steps) * 100 : 0;

  return (
    <div className="surface-card mb-4 animate-enter">
      <div className="p-5">
        {/* Header */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1 min-w-0 mr-3">
            <p className="text-sm font-semibold text-[var(--text-high)] truncate">
              {run.instruction.substring(0, 80)}{run.instruction.length > 80 ? '…' : ''}
            </p>
            <span className="text-xs text-[var(--text-low)]">
              {new Date(run.created_at).toLocaleString()} · {run.total_steps} steps
            </span>
          </div>
          <Badge variant={STATUS_VARIANTS[run.status] || 'secondary'} className="shrink-0">
            {run.status}
          </Badge>
        </div>

        {/* Progress */}
        {run.status === 'executing' && (
          <Progress value={progress} className="mb-3 h-1" />
        )}

        {/* Steps timeline */}
        {run.steps.length > 0 && (
          <div className="mt-3 space-y-0 border-l-2 border-[var(--border)] ml-2 pl-4">
            {run.steps.map((step, idx) => {
              let stepOutput = '';
              if (step.output_json) {
                try {
                  const parsed = typeof step.output_json === 'string' ? JSON.parse(step.output_json) : step.output_json;
                  stepOutput = parsed?.output || '';
                } catch {
                  stepOutput = '';
                }
              }
              return (
                <div key={step.id} className="relative pb-3 last:pb-0">
                  {/* Timeline dot */}
                  <span
                    className={`absolute -left-[21px] top-1.5 w-2.5 h-2.5 rounded-full border-2 border-[var(--bg-surface)] ${STATUS_COLORS[step.status] || 'bg-[var(--text-low)]'}`}
                  />
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-[var(--text-high)]">
                        {idx + 1}. {ACTION_LABELS[step.action] || step.action}
                      </p>
                      <p className="text-xs text-[var(--text-low)] mt-0.5">{step.description}</p>
                    </div>
                    {stepOutput && (
                      <button
                        type="button"
                        onClick={() => setSelectedStep(step)}
                        className="shrink-0 text-xs text-[var(--accent)] hover:underline flex items-center gap-0.5"
                      >
                        View <ChevronRight className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                  {stepOutput && (
                    <button
                      type="button"
                      onClick={() => setSelectedStep(step)}
                      className="mt-1.5 w-full text-left p-2.5 bg-[var(--bg-elevated)] rounded-lg text-xs text-[var(--text-mid)] whitespace-pre-wrap max-h-16 overflow-hidden truncate"
                    >
                      {stepOutput.substring(0, 160)}{stepOutput.length > 160 ? '…' : ''}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {run.error && (
          <Alert variant="destructive" className="mt-3">
            <AlertDescription>{run.error}</AlertDescription>
          </Alert>
        )}
      </div>
      <StepOutputDialog step={selectedStep} open={!!selectedStep} onClose={() => setSelectedStep(null)} />
    </div>
  );
}

export default function AgentsPage() {
  const [instruction, setInstruction] = useState('');
  const { data: runs, isLoading } = useAgentRuns();
  const runMutation = useRunAgent();

  const handleRun = () => {
    if (!instruction.trim()) return;
    runMutation.mutate(instruction.trim(), {
      onSuccess: () => { setInstruction(''); },
    });
  };

  return (
    <div className="p-5 space-y-5 animate-enter">

      {/* Page Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
          <Bot className="h-5 w-5 text-[var(--accent)]" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">AI Agents</h1>
          <p className="text-xs text-[var(--text-mid)]">Autonomous multi-step task execution</p>
        </div>
      </div>

      {/* Task Input */}
      <div className="surface-card p-5">
        <h2 className="text-sm font-semibold text-[var(--text-high)] mb-3 flex items-center gap-2">
          <Zap className="h-4 w-4 text-[var(--accent)]" />
          New Agent Task
        </h2>
        <Textarea
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          placeholder="Describe what you want the agent to do…"
          rows={3}
          className="mb-3"
        />

        {/* Suggestion chips */}
        <div className="flex gap-2 flex-wrap mb-4">
          <span className="text-xs text-[var(--text-low)] self-center">Try:</span>
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setInstruction(s)}
              className="text-xs px-2.5 py-1 rounded-full border border-[var(--border)] text-[var(--text-mid)]
                         hover:border-[var(--accent)]/50 hover:text-[var(--accent)] hover:bg-[var(--accent)]/5
                         transition-all duration-150"
            >
              {s}
            </button>
          ))}
        </div>

        <Button
          onClick={handleRun}
          disabled={!instruction.trim() || runMutation.isPending}
        >
          {runMutation.isPending ? (
            <span className="flex items-center gap-2">
              <Spinner size={16} className="text-current" />
              Running…
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Run Agent
            </span>
          )}
        </Button>

        {runMutation.isError && (
          <Alert variant="destructive" className="mt-4">
            <AlertDescription>{runMutation.error?.message}</AlertDescription>
          </Alert>
        )}
      </div>

      {/* Latest Result */}
      {runMutation.data && (
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-high)] mb-3 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse" />
            Latest Result
          </h2>
          <RunCard run={runMutation.data} />
        </div>
      )}

      {/* History */}
      <div>
        <h2 className="text-sm font-semibold text-[var(--text-high)] mb-3 flex items-center gap-2">
          <History className="h-4 w-4 text-[var(--text-low)]" />
          History
        </h2>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => <Skeleton key={i} className="h-[120px] w-full" />)}
          </div>
        ) : !runs?.length ? (
          <div className="surface-card p-8 text-center">
            <Bot className="h-10 w-10 text-[var(--text-low)] mx-auto mb-3 opacity-40" />
            <p className="text-sm font-medium text-[var(--text-mid)]">No agent runs yet</p>
            <p className="text-xs text-[var(--text-low)] mt-1">
              Run your first agent task above to see results here.
            </p>
          </div>
        ) : (
          runs.map((run) => <RunCard key={run.id} run={run} />)
        )}
      </div>

    </div>
  );
}
