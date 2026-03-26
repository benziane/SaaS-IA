'use client';

import { useState } from 'react';
import { Brain, Database, Rocket, BarChart3, Sparkles, Trash2, Loader2 } from 'lucide-react';

import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/lib/design-hub/components/Select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
} from '@/lib/design-hub/components/Dialog';

import {
  useAssessQuality, useAvailableModels, useCreateFromSource,
  useCreateFTJob, useDeleteFTDataset, useFTDatasets, useFTJobs,
} from '@/features/fine-tuning/hooks/useFineTuning';

const STATUS_VARIANTS: Record<string, 'secondary' | 'default' | 'success' | 'destructive' | 'warning' | 'outline'> = {
  draft: 'secondary',
  preparing: 'outline',
  training: 'warning',
  evaluating: 'outline',
  completed: 'success',
  failed: 'destructive',
  ready: 'success',
  cancelled: 'secondary',
};

const SOURCE_OPTIONS = [
  { id: 'transcriptions', label: 'Transcriptions', icon: '🎤' },
  { id: 'conversations', label: 'Chat Conversations', icon: '💬' },
  { id: 'documents', label: 'Knowledge Base Documents', icon: '📄' },
  { id: 'knowledge_qa', label: 'Knowledge Base Q&A', icon: '❓' },
];

export default function FineTuningPage() {
  const { data: datasets, isLoading: dsLoading } = useFTDatasets();
  const { data: jobs, isLoading: jobsLoading } = useFTJobs();
  const { data: models } = useAvailableModels();
  const createFromSourceMutation = useCreateFromSource();
  const deleteDsMutation = useDeleteFTDataset();
  const assessMutation = useAssessQuality();
  const createJobMutation = useCreateFTJob();

  const [sourceOpen, setSourceOpen] = useState(false);
  const [sourceName, setSourceName] = useState('');
  const [sourceType, setSourceType] = useState('transcriptions');
  const [maxSamples, setMaxSamples] = useState(100);

  const [trainOpen, setTrainOpen] = useState(false);
  const [trainName, setTrainName] = useState('');
  const [trainDataset, setTrainDataset] = useState('');
  const [trainModel, setTrainModel] = useState('llama-3.3-8b');
  const [trainEpochs, setTrainEpochs] = useState(3);

  const handleCreateFromSource = () => {
    if (!sourceName.trim()) return;
    createFromSourceMutation.mutate(
      { name: sourceName, source_type: sourceType, max_samples: maxSamples },
      { onSuccess: () => { setSourceOpen(false); setSourceName(''); } },
    );
  };

  const handleTrain = () => {
    if (!trainName.trim() || !trainDataset) return;
    createJobMutation.mutate(
      { name: trainName, dataset_id: trainDataset, base_model: trainModel, hyperparams: { epochs: trainEpochs } },
      { onSuccess: () => { setTrainOpen(false); setTrainName(''); } },
    );
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-[var(--text-high)]">
            <Brain className="h-7 w-7 text-[var(--accent)]" /> Fine-Tuning Studio
          </h1>
          <p className="text-sm text-[var(--text-mid)]">
            Create datasets from your platform data, train custom AI models, evaluate and deploy
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setSourceOpen(true)}>
            <Database className="h-4 w-4 mr-2" />
            Create Dataset
          </Button>
          <Button onClick={() => setTrainOpen(true)}
            disabled={!datasets?.some((d) => d.status === 'ready')}>
            <Rocket className="h-4 w-4 mr-2" />
            Train Model
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Datasets */}
        <div className="md:col-span-5">
          <Card>
            <CardContent className="p-6">
              <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">Training Datasets</h2>
              {dsLoading ? <Skeleton className="h-[200px] w-full" /> : !datasets?.length ? (
                <div className="text-center py-8">
                  <Database className="h-12 w-12 text-[var(--text-low)] mb-2 mx-auto" />
                  <p className="text-[var(--text-mid)]">No datasets yet</p>
                  <p className="text-xs text-[var(--text-mid)]">
                    Create one from your transcriptions, conversations, or documents
                  </p>
                </div>
              ) : (
                datasets.map((ds) => (
                  <Card key={ds.id} className="mb-2">
                    <CardContent className="py-3 px-4">
                      <div className="flex justify-between mb-1">
                        <h4 className="text-sm font-semibold text-[var(--text-high)]">{ds.name}</h4>
                        <div className="flex gap-1 items-center">
                          <Badge variant={STATUS_VARIANTS[ds.status] || 'secondary'}>{ds.status}</Badge>
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-red-400 hover:text-red-300" onClick={() => deleteDsMutation.mutate(ds.id)}>
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>
                      <div className="flex gap-1 flex-wrap">
                        <Badge variant="outline" className="text-xs">{ds.source_type}</Badge>
                        <Badge variant="outline" className="text-xs">{ds.sample_count} samples</Badge>
                        <Badge variant="outline" className="text-xs">{ds.dataset_type}</Badge>
                        {ds.quality_score !== null && (
                          <Badge variant={ds.quality_score > 0.7 ? 'success' : 'warning'} className="text-xs">
                            Quality: {(ds.quality_score * 100).toFixed(0)}%
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                    <CardFooter className="pt-0 px-4 pb-3">
                      <Button variant="ghost" size="sm"
                        onClick={() => assessMutation.mutate(ds.id)}
                        disabled={assessMutation.isPending || ds.status !== 'ready'}>
                        <BarChart3 className="h-4 w-4 mr-1" />
                        Assess Quality
                      </Button>
                    </CardFooter>
                  </Card>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Training Jobs */}
        <div className="md:col-span-7">
          <Card>
            <CardContent className="p-6">
              <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">Training Jobs</h2>
              {jobsLoading ? <Skeleton className="h-[300px] w-full" /> : !jobs?.length ? (
                <div className="text-center py-12">
                  <Brain className="h-16 w-16 text-[var(--text-low)] mb-4 mx-auto" />
                  <h3 className="text-lg font-semibold text-[var(--text-mid)]">No training jobs yet</h3>
                  <p className="text-sm text-[var(--text-mid)]">
                    Create a dataset first, then start training
                  </p>
                </div>
              ) : (
                jobs.map((job) => {
                  const metrics = JSON.parse(job.metrics_json || '{}');
                  return (
                    <Card key={job.id} className="mb-4">
                      <CardContent className="p-4">
                        <div className="flex justify-between mb-2">
                          <h4 className="text-base font-bold text-[var(--text-high)]">{job.name}</h4>
                          <Badge variant={STATUS_VARIANTS[job.status] || 'secondary'}>{job.status}</Badge>
                        </div>
                        <div className="flex gap-1 mb-3 flex-wrap">
                          <Badge variant="outline">{job.base_model}</Badge>
                          <Badge variant="outline">{job.provider}</Badge>
                          <Badge variant="outline">{job.epochs_completed}/{job.total_epochs} epochs</Badge>
                          {job.estimated_cost_usd > 0 && (
                            <Badge variant="outline">~${job.actual_cost_usd || job.estimated_cost_usd}</Badge>
                          )}
                        </div>
                        {(job.status === 'training' || job.status === 'preparing') && (
                          <Progress value={(job.epochs_completed / job.total_epochs) * 100} className="mb-2" />
                        )}
                        {metrics.final_loss !== undefined && (
                          <p className="text-xs text-[var(--text-mid)]">
                            Loss: {metrics.final_loss} | Eval Loss: {metrics.eval_loss}
                          </p>
                        )}
                        {job.result_model_id && (
                          <Alert variant="success" className="mt-2 py-1">
                            <AlertDescription className="text-xs">Model ID: {job.result_model_id}</AlertDescription>
                          </Alert>
                        )}
                        {job.error && (
                          <Alert variant="destructive" className="mt-2 py-1">
                            <AlertDescription>{job.error}</AlertDescription>
                          </Alert>
                        )}
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </CardContent>
          </Card>

          {/* Available Models */}
          {models && (
            <Card className="mt-4">
              <CardContent className="p-6">
                <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">Available Base Models</h2>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {models.map((m) => (
                    <Card key={m.id} className="p-3">
                      <h4 className="text-sm font-semibold text-[var(--text-high)]">{m.name}</h4>
                      <p className="text-xs text-[var(--text-mid)]">{m.parameters} params</p>
                      <div className="flex gap-1 mt-1">
                        <Badge variant="outline" className="text-xs">{m.provider}</Badge>
                        {m.supports_lora && <Badge variant="success" className="text-xs">LoRA</Badge>}
                      </div>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Create Dataset from Source */}
      <Dialog open={sourceOpen} onOpenChange={(v) => { if (!v) setSourceOpen(false); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Create Dataset from Platform Data</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1 block">Dataset Name</label>
              <Input value={sourceName} onChange={(e) => setSourceName(e.target.value)} placeholder="Dataset name" />
            </div>
            <div>
              <label className="text-sm font-semibold text-[var(--text-high)] mb-2 block">Data Source</label>
              <div className="flex flex-wrap gap-1">
                {SOURCE_OPTIONS.map((s) => (
                  <Badge
                    key={s.id}
                    variant={sourceType === s.id ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => setSourceType(s.id)}
                  >
                    {s.icon} {s.label}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1 block">Max Samples</label>
              <Input type="number" value={maxSamples} onChange={(e) => setMaxSamples(Number(e.target.value))} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setSourceOpen(false)}>Cancel</Button>
            <Button onClick={handleCreateFromSource}
              disabled={!sourceName.trim() || createFromSourceMutation.isPending}>
              {createFromSourceMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Sparkles className="h-4 w-4 mr-1" />}
              Create Dataset
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Train Model */}
      <Dialog open={trainOpen} onOpenChange={(v) => { if (!v) setTrainOpen(false); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Train Custom Model</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1 block">Model Name</label>
              <Input value={trainName} onChange={(e) => setTrainName(e.target.value)} placeholder="Model name" />
            </div>
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1 block">Dataset</label>
              <Select value={trainDataset} onValueChange={setTrainDataset}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a dataset" />
                </SelectTrigger>
                <SelectContent>
                  {datasets?.filter((d) => d.status === 'ready').map((d) => (
                    <SelectItem key={d.id} value={d.id}>{d.name} ({d.sample_count} samples)</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1 block">Base Model</label>
              <Select value={trainModel} onValueChange={setTrainModel}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a model" />
                </SelectTrigger>
                <SelectContent>
                  {models?.map((m) => (
                    <SelectItem key={m.id} value={m.id}>{m.name} ({m.parameters})</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1 block">Epochs</label>
              <Input type="number" value={trainEpochs} onChange={(e) => setTrainEpochs(Number(e.target.value))}
                min={1} max={10} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setTrainOpen(false)}>Cancel</Button>
            <Button onClick={handleTrain}
              disabled={!trainName.trim() || !trainDataset || createJobMutation.isPending}>
              {createJobMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Rocket className="h-4 w-4 mr-1" />}
              Start Training
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
