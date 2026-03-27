'use client';

import { useState } from 'react';
import { CheckCircle2, Clock, Copy, Loader2, Play, Plus, Sparkles, Trash2, Workflow, XCircle, AlertCircle } from 'lucide-react';

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

const RUN_STATUS_ICON: Record<string, React.ReactNode> = {
  completed: <CheckCircle2 className="h-4 w-4 text-green-400" />,
  failed: <XCircle className="h-4 w-4 text-red-400" />,
  running: <Loader2 className="h-4 w-4 animate-spin text-[var(--accent)]" />,
  pending: <Clock className="h-4 w-4 text-[var(--text-mid)]" />,
  cancelled: <XCircle className="h-4 w-4 text-yellow-400" />,
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
    <div className="p-5 space-y-5 animate-enter">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
            <Workflow className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">AI Workflows</h1>
            <p className="text-xs text-[var(--text-mid)]">Build no-code AI automation workflows with triggers, actions, and templates</p>
          </div>
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

      {/* Quick Start Templates */}
      {templates && templates.length > 0 && !workflows?.length && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-[var(--text-high)]">Quick Start with Templates</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {templates.slice(0, 3).map((template) => (
              <div
                key={template.id}
                className="surface-card border-glow-accent rounded-xl p-4 cursor-pointer hover:border-[var(--accent)] transition-colors"
                onClick={() => handleUseTemplate(template.id)}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
                    <Sparkles className="h-3.5 w-3.5 text-white" />
                  </div>
                  <h4 className="text-sm font-bold text-[var(--text-high)]">{template.name}</h4>
                </div>
                <p className="text-xs text-[var(--text-mid)] mb-3 line-clamp-2">{template.description}</p>
                <div className="flex gap-1 flex-wrap">
                  <Badge variant="outline">{template.category}</Badge>
                  <Badge variant="outline">{template.nodes.length} steps</Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Workflows Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-[220px] w-full rounded-xl" />
          ))}
        </div>
      ) : !workflows?.length ? (
        <div className="surface-card rounded-xl text-center py-16 px-6">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] mx-auto mb-4">
            <Workflow className="h-7 w-7 text-white" />
          </div>
          <h3 className="text-base font-semibold text-[var(--text-high)]">No workflows yet</h3>
          <p className="text-sm text-[var(--text-mid)] mt-2 mb-5">
            Create a workflow from scratch or use a template to get started
          </p>
          <div className="flex gap-2 justify-center">
            <Button variant="outline" onClick={() => setTemplatesOpen(true)}>Browse Templates</Button>
            <Button onClick={() => setCreateOpen(true)}>Create Blank</Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
          {workflows.map((workflow) => (
            <div key={workflow.id} className="surface-card border-glow-accent rounded-xl p-4 flex flex-col gap-3">
              {/* Card Header */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
                    <Workflow className="h-3.5 w-3.5 text-white" />
                  </div>
                  <h4 className="text-sm font-bold text-[var(--text-high)] truncate">{workflow.name}</h4>
                </div>
                <Badge variant={STATUS_VARIANTS[workflow.status] || 'secondary'} className="shrink-0">
                  {workflow.status}
                </Badge>
              </div>

              {workflow.description && (
                <p className="text-xs text-[var(--text-mid)] line-clamp-2">{workflow.description}</p>
              )}

              {/* Node flow preview */}
              <div className="flex flex-wrap gap-1">
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

              {/* Card Footer */}
              <div className="flex items-center justify-between pt-1 border-t border-[var(--border)]">
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-red-400 hover:text-red-300"
                    onClick={() => deleteMutation.mutate(workflow.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => setSelectedWorkflow(selectedWorkflow === workflow.id ? null : workflow.id)}
                  >
                    <Clock className="h-3.5 w-3.5" />
                  </Button>
                </div>
                <Button
                  size="sm"
                  onClick={() => handleTrigger(workflow.id)}
                  disabled={triggerMutation.isPending || workflow.nodes.length === 0}
                >
                  {triggerMutation.isPending
                    ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                    : <Play className="h-3.5 w-3.5 mr-1" />}
                  Run
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Run History Panel — timeline style */}
      {selectedWorkflow && runs && (
        <div className="surface-card rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-semibold text-[var(--text-high)]">Run History</h2>
          {runs.length === 0 ? (
            <p className="text-sm text-[var(--text-mid)]">No runs yet</p>
          ) : (
            <div className="relative space-y-0">
              {/* Vertical timeline line */}
              <div className="absolute left-[15px] top-2 bottom-2 w-px bg-[var(--border)]" />
              {runs.map((run) => (
                <div
                  key={run.id}
                  className="relative pl-9 pb-4 cursor-pointer group"
                  onClick={() => setRunResult(run)}
                >
                  {/* Timeline dot */}
                  <div className="absolute left-0 top-1 flex items-center justify-center w-[30px]">
                    {RUN_STATUS_ICON[run.status] ?? <Clock className="h-4 w-4 text-[var(--text-mid)]" />}
                  </div>

                  <div className="surface-card rounded-lg px-4 py-3 group-hover:border-[var(--accent)] transition-colors">
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
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
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
              <div
                key={template.id}
                className="surface-card border-glow-accent rounded-xl p-4 cursor-pointer hover:border-[var(--accent)] transition-colors"
                onClick={() => handleUseTemplate(template.id)}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
                    <Sparkles className="h-3.5 w-3.5 text-white" />
                  </div>
                  <h4 className="text-sm font-bold text-[var(--text-high)]">{template.name}</h4>
                </div>
                <p className="text-xs text-[var(--text-mid)] mb-3 line-clamp-2">{template.description}</p>
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
              </div>
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
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{triggerMutation.error?.message}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
