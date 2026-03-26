'use client';

import { useState } from 'react';
import { GitBranch, Play, Plus, Trash2, Clock, Sparkles, Copy, Loader2, AlertCircle } from 'lucide-react';

import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from '@/lib/design-hub/components/Dialog';

import {
  useCreateFromTemplate,
  useCreateWorkflow,
  useDeleteWorkflow,
  useTemplates,
  useTriggerWorkflow,
  useWorkflowRuns,
  useWorkflows,
} from '@/features/workflows/hooks/useWorkflows';
import type { WorkflowRun } from '@/features/workflows/types';

const STATUS_VARIANTS: Record<string, 'secondary' | 'default' | 'success' | 'destructive' | 'warning' | 'outline'> = {
  draft: 'secondary',
  active: 'default',
  paused: 'warning',
  archived: 'secondary',
  pending: 'secondary',
  running: 'outline',
  completed: 'success',
  failed: 'destructive',
  cancelled: 'warning',
};

const TRIGGER_LABELS: Record<string, string> = {
  manual: 'Manual',
  webhook: 'Webhook',
  schedule: 'Scheduled',
  new_transcription: 'New Transcription',
  new_document: 'New Document',
  new_content: 'New Content',
  keyword_alert: 'Keyword Alert',
};

const ACTION_ICONS: Record<string, string> = {
  transcribe: '🎤',
  summarize: '📋',
  translate: '🌐',
  sentiment: '💭',
  generate: '🤖',
  crawl: '🕷️',
  search_knowledge: '🔍',
  index_knowledge: '📚',
  compare: '⚖️',
  content_studio: '✨',
  notify: '🔔',
  webhook_call: '🔗',
  condition: '❓',
};

export default function WorkflowsPage() {
  const { data: workflows, isLoading } = useWorkflows();
  const { data: templates } = useTemplates();
  const createMutation = useCreateWorkflow();
  const createFromTemplateMutation = useCreateFromTemplate();
  const deleteMutation = useDeleteWorkflow();
  const triggerMutation = useTriggerWorkflow();

  const [createOpen, setCreateOpen] = useState(false);
  const [templatesOpen, setTemplatesOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<WorkflowRun | null>(null);
  const [inputText, setInputText] = useState('');
  const [runOpen, setRunOpen] = useState(false);
  const [runWorkflowId, setRunWorkflowId] = useState<string | null>(null);

  const { data: runs } = useWorkflowRuns(selectedWorkflow);

  const handleCreateBlank = () => {
    if (!newName.trim()) return;
    createMutation.mutate(
      { name: newName, description: newDesc || undefined, nodes: [], edges: [] },
      {
        onSuccess: () => {
          setCreateOpen(false);
          setNewName('');
          setNewDesc('');
        },
      }
    );
  };

  const handleUseTemplate = (templateId: string) => {
    createFromTemplateMutation.mutate(
      { templateId },
      { onSuccess: () => setTemplatesOpen(false) }
    );
  };

  const handleTrigger = (workflowId: string) => {
    setRunWorkflowId(workflowId);
    setInputText('');
    setRunOpen(true);
  };

  const handleRunConfirm = () => {
    if (!runWorkflowId) return;
    const inputData = inputText.trim() ? { text: inputText } : undefined;
    triggerMutation.mutate(
      { id: runWorkflowId, inputData },
      { onSuccess: (run) => { setRunResult(run); setRunOpen(false); } }
    );
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-[var(--text-high)]">
            <GitBranch className="h-7 w-7 text-[var(--accent)]" /> AI Workflows
          </h1>
          <p className="text-sm text-[var(--text-mid)]">
            Build no-code AI automation workflows with triggers, actions, and templates
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setTemplatesOpen(true)}>
            <Sparkles className="h-4 w-4 mr-2" />
            Templates
          </Button>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Workflow
          </Button>
        </div>
      </div>

      {/* Templates Section */}
      {templates && templates.length > 0 && !workflows?.length && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">Quick Start with Templates</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {templates.slice(0, 3).map((template) => (
              <Card
                key={template.id}
                className="cursor-pointer hover:border-[var(--accent)] hover:bg-[var(--bg-elevated)] transition-colors"
                onClick={() => handleUseTemplate(template.id)}
              >
                <CardContent className="p-4">
                  <h4 className="text-base font-bold text-[var(--text-high)]">{template.name}</h4>
                  <p className="text-sm text-[var(--text-mid)] mt-1 mb-2">
                    {template.description}
                  </p>
                  <div className="flex gap-1">
                    <Badge variant="outline">{template.category}</Badge>
                    <Badge variant="outline">{template.nodes.length} steps</Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Workflows Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-[220px] w-full rounded" />
          ))}
        </div>
      ) : !workflows?.length ? (
        <Card>
          <CardContent className="text-center py-16">
            <GitBranch className="h-16 w-16 text-[var(--text-low)] mb-4 mx-auto" />
            <h3 className="text-lg font-semibold text-[var(--text-mid)]">No workflows yet</h3>
            <p className="text-sm text-[var(--text-mid)] mt-2 mb-4">
              Create a workflow from scratch or use a template to get started
            </p>
            <div className="flex gap-2 justify-center">
              <Button variant="outline" onClick={() => setTemplatesOpen(true)}>Browse Templates</Button>
              <Button onClick={() => setCreateOpen(true)}>Create Blank</Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {workflows.map((workflow) => (
            <Card key={workflow.id} className="h-full flex flex-col">
              <CardContent className="p-4 flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-base font-bold text-[var(--text-high)] truncate">
                    {workflow.name}
                  </h4>
                  <Badge variant={STATUS_VARIANTS[workflow.status] || 'secondary'}>
                    {workflow.status}
                  </Badge>
                </div>
                {workflow.description && (
                  <p className="text-sm text-[var(--text-mid)] mb-3 line-clamp-2">
                    {workflow.description}
                  </p>
                )}

                {/* Node flow preview */}
                <div className="flex flex-wrap gap-1 mb-3">
                  {workflow.nodes.map((node, i) => (
                    <div key={node.id} className="flex items-center gap-1">
                      <Badge variant="outline" className="text-xs">
                        {ACTION_ICONS[node.action] || '⚙️'} {node.label || node.action}
                      </Badge>
                      {i < workflow.nodes.length - 1 && (
                        <span className="text-xs text-[var(--text-low)]">&rarr;</span>
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex gap-1 flex-wrap">
                  <Badge variant="outline">{TRIGGER_LABELS[workflow.trigger_type] || workflow.trigger_type}</Badge>
                  <Badge variant="outline">{workflow.run_count} runs</Badge>
                  {workflow.template_category && (
                    <Badge variant="default">{workflow.template_category}</Badge>
                  )}
                </div>
              </CardContent>
              <CardFooter className="flex justify-between px-4 pb-4">
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" className="text-red-400 hover:text-red-300" onClick={() => deleteMutation.mutate(workflow.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => setSelectedWorkflow(selectedWorkflow === workflow.id ? null : workflow.id)}>
                    <Clock className="h-4 w-4" />
                  </Button>
                </div>
                <Button
                  size="sm"
                  onClick={() => handleTrigger(workflow.id)}
                  disabled={triggerMutation.isPending || workflow.nodes.length === 0}
                >
                  {triggerMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Play className="h-4 w-4 mr-1" />}
                  Run
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Run History Panel */}
      {selectedWorkflow && runs && (
        <Card className="mt-6">
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">Run History</h2>
            {runs.length === 0 ? (
              <p className="text-[var(--text-mid)]">No runs yet</p>
            ) : (
              runs.map((run) => (
                <Card key={run.id} className="mb-2 cursor-pointer hover:border-[var(--accent)] transition-colors" onClick={() => setRunResult(run)}>
                  <CardContent className="py-3 px-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant={STATUS_VARIANTS[run.status] || 'secondary'}>{run.status}</Badge>
                        <span className="text-sm text-[var(--text-high)]">
                          {run.current_node}/{run.total_nodes} nodes
                        </span>
                        {run.duration_ms && (
                          <span className="text-xs text-[var(--text-mid)]">
                            {(run.duration_ms / 1000).toFixed(1)}s
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-[var(--text-mid)]">
                        {new Date(run.created_at).toLocaleString()}
                      </span>
                    </div>
                    {run.status === 'running' && (
                      <Progress className="mt-2" value={(run.current_node / run.total_nodes) * 100} />
                    )}
                    {run.error && (
                      <Alert variant="destructive" className="mt-2 py-1">
                        <AlertDescription>{run.error}</AlertDescription>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {/* Run Input Dialog */}
      <Dialog open={runOpen} onOpenChange={(v) => { if (!v) setRunOpen(false); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Run Workflow</DialogTitle>
            <DialogDescription>
              Optionally provide input text/data for the first node of the workflow.
            </DialogDescription>
          </DialogHeader>
          <Textarea
            rows={4}
            placeholder="Enter text, URL, or data to process..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />
          <DialogFooter>
            <Button variant="ghost" onClick={() => setRunOpen(false)}>Cancel</Button>
            <Button
              onClick={handleRunConfirm}
              disabled={triggerMutation.isPending}
            >
              {triggerMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Play className="h-4 w-4 mr-1" />}
              Run Now
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Run Result Dialog */}
      <Dialog open={!!runResult} onOpenChange={(v) => { if (!v) setRunResult(null); }}>
        <DialogContent className="max-w-2xl">
          {runResult && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  Workflow Run
                  <Badge variant={STATUS_VARIANTS[runResult.status] || 'secondary'}>{runResult.status}</Badge>
                  {runResult.duration_ms && (
                    <Badge variant="outline">{(runResult.duration_ms / 1000).toFixed(1)}s</Badge>
                  )}
                </DialogTitle>
              </DialogHeader>
              <div className="border-t border-[var(--border)] pt-4 max-h-[60vh] overflow-y-auto space-y-4">
                {runResult.results.length > 0 ? (
                  runResult.results.map((result: Record<string, unknown>, i: number) => (
                    <div key={i} className="pl-4 border-l-2 border-[var(--accent)]">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-sm font-semibold text-[var(--text-high)]">
                          {ACTION_ICONS[(result.action as string) || ''] || '⚙️'}{' '}
                          {(result.label as string) || (result.action as string) || `Step ${i + 1}`}
                        </h4>
                        {Boolean(result.error) && <Badge variant="destructive">error</Badge>}
                      </div>
                      {Boolean(result.output) && (
                        <div className="relative">
                          <div className="bg-[var(--bg-elevated)] rounded p-3 text-sm whitespace-pre-wrap max-h-[200px] overflow-auto break-words">
                            {(result.output as string).substring(0, 1000)}
                            {(result.output as string).length > 1000 && '...'}
                          </div>
                          <button
                            type="button"
                            title="Copy to clipboard"
                            className="absolute top-2 right-2 p-1 rounded hover:bg-[var(--bg-surface)]"
                            onClick={() => navigator.clipboard.writeText(result.output as string)}
                          >
                            <Copy className="h-3 w-3 text-[var(--text-mid)]" />
                          </button>
                        </div>
                      )}
                      {Boolean(result.error) && (
                        <Alert variant="destructive" className="mt-2">
                          <AlertDescription>{result.error as string}</AlertDescription>
                        </Alert>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-[var(--text-mid)]">No results yet</p>
                )}
                {runResult.error && (
                  <Alert variant="destructive" className="mt-4">
                    <AlertDescription>{runResult.error}</AlertDescription>
                  </Alert>
                )}
              </div>
              <DialogFooter>
                <Button variant="ghost" onClick={() => setRunResult(null)}>Close</Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Templates Dialog */}
      <Dialog open={templatesOpen} onOpenChange={(v) => { if (!v) setTemplatesOpen(false); }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Workflow Templates</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
            {templates?.map((template) => (
              <Card
                key={template.id}
                className="cursor-pointer hover:border-[var(--accent)] hover:bg-[var(--bg-elevated)] transition-colors"
                onClick={() => handleUseTemplate(template.id)}
              >
                <CardContent className="p-4">
                  <h4 className="text-base font-bold text-[var(--text-high)]">{template.name}</h4>
                  <p className="text-sm text-[var(--text-mid)] mt-1 mb-3">
                    {template.description}
                  </p>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {template.nodes.map((node, i) => (
                      <div key={node.id} className="flex items-center gap-1">
                        <Badge variant="outline" className="text-xs">
                          {ACTION_ICONS[node.action] || '⚙️'} {node.label}
                        </Badge>
                        {i < template.nodes.length - 1 && (
                          <span className="text-xs text-[var(--text-low)]">&rarr;</span>
                        )}
                      </div>
                    ))}
                  </div>
                  <Badge variant="default">{template.category}</Badge>
                </CardContent>
              </Card>
            ))}
          </div>
          {createFromTemplateMutation.isPending && (
            <div className="flex justify-center mt-4">
              <Loader2 className="h-6 w-6 animate-spin text-[var(--accent)]" />
            </div>
          )}
          <DialogFooter>
            <Button variant="ghost" onClick={() => setTemplatesOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Blank Dialog */}
      <Dialog open={createOpen} onOpenChange={(v) => { if (!v) setCreateOpen(false); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>New Workflow</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1 block">Workflow Name</label>
              <Input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Workflow name"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1 block">Description (optional)</label>
              <Textarea
                rows={2}
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Description"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCreateBlank}
              disabled={!newName.trim() || createMutation.isPending}
            >
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {triggerMutation.isError && (
        <Alert variant="destructive" className="mt-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{triggerMutation.error?.message}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
