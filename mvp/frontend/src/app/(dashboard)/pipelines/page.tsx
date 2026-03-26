'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';

import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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

const STATUS_COLORS: Record<string, 'default' | 'secondary' | 'success' | 'destructive' | 'warning'> = {
  draft: 'secondary',
  active: 'default',
  archived: 'warning',
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
      <div className="p-6">
        <Skeleton className="w-48 h-10 mb-4" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-[180px]" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertDescription>Failed to load pipelines.</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-[var(--text-high)]">AI Pipelines</h1>
        <Button onClick={() => setCreateOpen(true)}>
          Create Pipeline
        </Button>
      </div>

      {execResult && (
        <Alert
          variant={execResult.status === 'completed' ? 'success' : execResult.status === 'failed' ? 'destructive' : 'info'}
          className="mb-6"
        >
          <AlertDescription>
            Pipeline execution {execResult.status}.
            {execResult.error && ` Error: ${execResult.error}`}
            {execResult.status === 'completed' && ` (${execResult.total_steps} steps completed)`}
          </AlertDescription>
        </Alert>
      )}

      {!pipelines?.length ? (
        <Card>
          <CardContent className="text-center py-12">
            <h2 className="text-lg font-semibold text-[var(--text-mid)] mb-2">
              No pipelines yet
            </h2>
            <p className="text-sm text-[var(--text-mid)] mb-4">
              Create your first AI pipeline to chain operations like transcription, summarization, and translation.
            </p>
            <Button variant="outline" onClick={() => setCreateOpen(true)}>
              Create Pipeline
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {pipelines.map((pipeline) => (
            <Card key={pipeline.id} className="flex flex-col h-full border border-[var(--border)]">
              <CardContent className="flex-1 p-6">
                <div className="flex justify-between mb-2">
                  <h3 className="text-lg font-semibold text-[var(--text-high)] truncate">
                    {pipeline.name}
                  </h3>
                  <Badge variant={STATUS_COLORS[pipeline.status] || 'secondary'}>
                    {pipeline.status}
                  </Badge>
                </div>
                {pipeline.description && (
                  <p className="text-sm text-[var(--text-mid)] mb-2">
                    {pipeline.description}
                  </p>
                )}
                <p className="text-xs text-[var(--text-low)]">
                  {pipeline.steps.length} steps
                </p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {pipeline.steps.map((step) => (
                    <Badge key={step.id} variant="outline" className="text-xs">
                      {step.type}
                    </Badge>
                  ))}
                </div>
              </CardContent>
              <CardFooter className="gap-2">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleExecute(pipeline.id)}
                  disabled={executeMutation.isPending}
                >
                  {executeMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Execute'}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-red-400 hover:text-red-300"
                  onClick={() => deleteMutation.mutate(pipeline.id)}
                  disabled={deleteMutation.isPending}
                >
                  Delete
                </Button>
              </CardFooter>
            </Card>
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
                placeholder="Pipeline Name"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Description (optional)</label>
              <Textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Description (optional)"
                rows={2}
              />
            </div>
            <p className="text-sm text-[var(--text-mid)]">
              A default pipeline with Transcription and Summarize steps will be created.
              You can edit the steps later.
            </p>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCreate}
              disabled={!newName.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? 'Creating...' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
