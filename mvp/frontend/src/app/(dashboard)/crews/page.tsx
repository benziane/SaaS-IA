'use client';

import { useState } from 'react';
import { Users, Users2, Play, Trash2, Sparkles, Copy, Loader2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Separator } from '@/lib/design-hub/components/Separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
} from '@/lib/design-hub/components/Dialog';

import {
  useCreateFromTemplate, useCrewTemplates, useCrews,
  useDeleteCrew, useRunCrew,
} from '@/features/crews/hooks/useCrews';
import type { CrewRun } from '@/features/crews/types';

const ROLE_ICONS: Record<string, string> = {
  researcher: '🔬', writer: '✍️', reviewer: '📝', analyst: '📊',
  coder: '💻', translator: '🌐', summarizer: '📋', creative: '🎨', custom: '⚙️',
};

const STATUS_VARIANTS: Record<string, 'secondary' | 'default' | 'success' | 'destructive' | 'outline'> = {
  draft: 'secondary',
  active: 'default',
  pending: 'secondary',
  running: 'outline',
  completed: 'success',
  failed: 'destructive',
};

export default function CrewsPage() {
  const { data: crews, isLoading } = useCrews();
  const { data: templates } = useCrewTemplates();
  const deleteMutation = useDeleteCrew();
  const runMutation = useRunCrew();
  const templateMutation = useCreateFromTemplate();

  const [runOpen, setRunOpen] = useState(false);
  const [runCrewId, setRunCrewId] = useState<string | null>(null);
  const [instruction, setInstruction] = useState('');
  const [runResult, setRunResult] = useState<CrewRun | null>(null);
  const [templatesOpen, setTemplatesOpen] = useState(false);

  const handleRun = () => {
    if (!runCrewId || !instruction.trim()) return;
    runMutation.mutate(
      { id: runCrewId, instruction },
      { onSuccess: (run) => { setRunResult(run); setRunOpen(false); } },
    );
  };

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
            <Users2 className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">AI Agent Crews</h1>
            <p className="text-xs text-[var(--text-mid)]">Multi-agent crew coordination</p>
          </div>
        </div>
        <Button variant="outline" onClick={() => setTemplatesOpen(true)}>
          <Sparkles className="h-4 w-4 mr-2" />
          Templates
        </Button>
      </div>

      {/* Templates quick start */}
      {!crews?.length && templates && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {templates.map((t) => (
            <div
              key={t.id}
              className="surface-card p-5 cursor-pointer hover:border-[var(--accent)] transition-colors"
              onClick={() => templateMutation.mutate({ templateId: t.id })}
            >
              <h4 className="text-sm font-bold text-[var(--text-high)]">{t.name}</h4>
              <p className="text-xs text-[var(--text-mid)]">{t.description}</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {t.agents.map((a) => (
                  <Badge key={a.id} variant="outline" className="text-xs">
                    {ROLE_ICONS[a.role] || '⚙️'} {a.name}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {isLoading ? (
        <Skeleton className="h-[300px] w-full" />
      ) : !crews?.length ? (
        <div className="surface-card p-5 text-center py-16">
          <Users className="h-16 w-16 text-[var(--text-low)] mb-4 mx-auto" />
          <h3 className="text-lg font-semibold text-[var(--text-mid)]">No crews yet</h3>
          <Button variant="ghost" className="mt-2" onClick={() => setTemplatesOpen(true)}>Use a Template</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {crews.map((crew) => (
            <div key={crew.id} className="surface-card p-5 flex flex-col gap-2">
              <div className="flex justify-between mb-2">
                <h4 className="text-base font-bold text-[var(--text-high)]">{crew.name}</h4>
                <Badge variant={STATUS_VARIANTS[crew.status] || 'secondary'}>{crew.status}</Badge>
              </div>
              {crew.goal && <p className="text-sm text-[var(--text-mid)]">{crew.goal}</p>}
              <div className="flex flex-wrap gap-1">
                {crew.agents.map((a) => (
                  <Badge key={a.id} variant="outline" className="text-xs">
                    {ROLE_ICONS[a.role] || '⚙️'} {a.name}
                  </Badge>
                ))}
              </div>
              <Badge variant="outline" className="text-xs w-fit">{crew.process_type} | {crew.run_count} runs</Badge>
              <div className="flex justify-between mt-auto pt-2">
                <Button variant="ghost" size="icon" className="text-red-400 hover:text-red-300" onClick={() => deleteMutation.mutate(crew.id)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
                <Button size="sm" onClick={() => { setRunCrewId(crew.id); setInstruction(''); setRunOpen(true); }}>
                  <Play className="h-4 w-4 mr-1" />
                  Run
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Run Dialog */}
      <Dialog open={runOpen} onOpenChange={(v) => { if (!v) setRunOpen(false); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Run Agent Crew</DialogTitle>
          </DialogHeader>
          <Textarea
            rows={4}
            placeholder="What should the crew accomplish?"
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            className="mt-2"
          />
          <DialogFooter>
            <Button variant="ghost" onClick={() => setRunOpen(false)}>Cancel</Button>
            <Button onClick={handleRun} disabled={!instruction.trim() || runMutation.isPending}>
              {runMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Play className="h-4 w-4 mr-1" />}
              Run Crew
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Result Dialog */}
      <Dialog open={!!runResult} onOpenChange={(v) => { if (!v) setRunResult(null); }}>
        <DialogContent className="max-w-2xl">
          {runResult && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  Crew Run
                  <Badge variant={STATUS_VARIANTS[runResult.status] || 'secondary'}>{runResult.status}</Badge>
                  {runResult.duration_ms && <Badge variant="outline">{(runResult.duration_ms / 1000).toFixed(1)}s</Badge>}
                </DialogTitle>
              </DialogHeader>
              <div className="border-t border-[var(--border)] pt-4 max-h-[60vh] overflow-y-auto space-y-4">
                {runResult.messages.map((msg, i) => (
                  <div key={i} className="pl-4 border-l-2 border-[var(--accent)]">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-sm font-semibold text-[var(--text-high)]">
                        {ROLE_ICONS[msg.role] || '⚙️'} {msg.agent_name} ({msg.role})
                      </h4>
                      {msg.tool_used && <Badge variant="outline" className="text-xs">tool: {msg.tool_used}</Badge>}
                    </div>
                    <div className="relative bg-[var(--bg-elevated)] rounded p-3 text-sm whitespace-pre-wrap max-h-[200px] overflow-auto">
                      {msg.content.substring(0, 1500)}{msg.content.length > 1500 && '...'}
                      <button type="button" title="Copy to clipboard" className="absolute top-2 right-2 p-1 rounded hover:bg-[var(--bg-surface)]"
                        onClick={() => navigator.clipboard.writeText(msg.content)}>
                        <Copy className="h-3 w-3 text-[var(--text-mid)]" />
                      </button>
                    </div>
                  </div>
                ))}
                {runResult.final_output && (
                  <>
                    <Separator className="my-4" />
                    <h4 className="text-sm font-semibold text-[var(--text-high)] mb-2">Final Output</h4>
                    <div className="p-4 bg-green-500/10 rounded whitespace-pre-wrap text-sm">{runResult.final_output}</div>
                  </>
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
            <DialogTitle>Crew Templates</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
            {templates?.map((t) => (
              <div
                key={t.id}
                className="surface-card p-5 cursor-pointer hover:border-[var(--accent)] transition-colors"
                onClick={() => { templateMutation.mutate({ templateId: t.id }); setTemplatesOpen(false); }}
              >
                <h4 className="text-base font-bold text-[var(--text-high)]">{t.name}</h4>
                <p className="text-sm text-[var(--text-mid)] mb-2">{t.description}</p>
                <div className="flex flex-wrap gap-1">
                  {t.agents.map((a) => (
                    <Badge key={a.id} variant="outline" className="text-xs">
                      {ROLE_ICONS[a.role] || '⚙️'} {a.name}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setTemplatesOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
