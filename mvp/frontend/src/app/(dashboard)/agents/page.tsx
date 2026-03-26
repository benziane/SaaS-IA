'use client';

import { useState } from 'react';


import { Card, CardContent } from '@/components/ui/card';
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
            {output || 'Pas de résultat disponible.'}
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
    <Card className="mb-4 border border-[var(--border)]">
      <CardContent className="p-6">
        <div className="flex justify-between items-start mb-2">
          <h6 className="text-base font-semibold text-[var(--text-high)] truncate">
            {run.instruction.substring(0, 80)}{run.instruction.length > 80 ? '...' : ''}
          </h6>
          <Badge variant={STATUS_VARIANTS[run.status] || 'secondary'}>{run.status}</Badge>
        </div>

        {run.status === 'executing' && (
          <Progress value={progress} className="mb-2 h-1.5" />
        )}

        <span className="text-xs text-[var(--text-mid)]">
          {run.total_steps} steps | {new Date(run.created_at).toLocaleString()}
        </span>

        {run.steps.length > 0 && (
          <div className="mt-2 space-y-0">
            {run.steps.map((step) => {
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
                <div key={step.id} className="py-1 flex flex-col">
                  <div className="flex justify-between items-center">
                    <div className="min-w-0">
                      <p className="text-sm text-[var(--text-high)]">
                        {step.step_index + 1}. {ACTION_LABELS[step.action] || step.action}
                      </p>
                      <span className="text-xs text-[var(--text-mid)]">{step.description}</span>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {stepOutput && (
                        <Button variant="ghost" size="sm" onClick={() => setSelectedStep(step)} className="text-xs px-2">
                          Voir
                        </Button>
                      )}
                      <Badge variant={STATUS_VARIANTS[step.status] || 'outline'}>{step.status}</Badge>
                    </div>
                  </div>
                  {stepOutput && (
                    <p
                      className="mt-1 mb-2 p-2 bg-[var(--bg-elevated)] rounded text-xs whitespace-pre-wrap max-h-20 overflow-hidden block cursor-pointer text-[var(--text-mid)]"
                      onClick={() => setSelectedStep(step)}
                    >
                      {stepOutput.substring(0, 200)}{stepOutput.length > 200 ? '… (cliquer pour voir tout)' : ''}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {run.error && (
          <Alert variant="destructive" className="mt-2">
            <AlertDescription>{run.error}</AlertDescription>
          </Alert>
        )}
      </CardContent>
      <StepOutputDialog step={selectedStep} open={!!selectedStep} onClose={() => setSelectedStep(null)} />
    </Card>
  );
}

export default function AgentsPage() {
  const [instruction, setInstruction] = useState('');
  const { data: runs, isLoading } = useAgentRuns();
  const runMutation = useRunAgent();

  const handleRun = () => {
    if (!instruction.trim()) { return; }
    runMutation.mutate(instruction.trim(), {
      onSuccess: () => { setInstruction(''); },
    });
  };

  return (
    <div className="p-6">
      <h4 className="text-2xl font-bold text-[var(--text-high)] mb-6">AI Agents</h4>

      <Card className="mb-6">
        <CardContent className="p-6">
          <h6 className="text-base font-semibold text-[var(--text-high)] mb-4">New Agent Task</h6>
          <Textarea
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="Describe what you want the agent to do..."
            rows={3}
            className="mb-4"
          />
          <div className="flex gap-2 flex-wrap mb-4">
            <span className="text-xs text-[var(--text-mid)] w-full">Try:</span>
            {[
              'Summarize my latest transcription',
              'Search knowledge base for meeting notes',
              'Analyze sentiment of a text about customer feedback',
              'Compare AI models on: explain quantum computing',
            ].map((suggestion) => (
              <Badge
                key={suggestion}
                variant="outline"
                className="cursor-pointer hover:bg-[var(--bg-elevated)]"
                onClick={() => setInstruction(suggestion)}
              >
                {suggestion}
              </Badge>
            ))}
          </div>
          <Button
            onClick={handleRun}
            disabled={!instruction.trim() || runMutation.isPending}
          >
            {runMutation.isPending ? (
              <span className="flex items-center gap-2">
                <Spinner size={16} className="text-current" />
                Running...
              </span>
            ) : 'Run Agent'}
          </Button>

          {runMutation.isError && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>{runMutation.error?.message}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {runMutation.data && (
        <div className="mb-6">
          <h6 className="text-base font-semibold text-[var(--text-high)] mb-2">Latest Result</h6>
          <RunCard run={runMutation.data} />
        </div>
      )}

      <h6 className="text-base font-semibold text-[var(--text-high)] mb-4">History</h6>
      {isLoading ? (
        <Skeleton className="h-[200px] w-full" />
      ) : !runs?.length ? (
        <p className="text-sm text-[var(--text-mid)]">No agent runs yet.</p>
      ) : (
        runs.map((run) => <RunCard key={run.id} run={run} />)
      )}
    </div>
  );
}
