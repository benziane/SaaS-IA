'use client';

import { useState } from 'react';
import {
  Alert, Box, Button, Card, CardActions, CardContent, Chip, CircularProgress,
  Dialog, DialogActions, DialogContent, DialogTitle,
  FormControl, Grid, InputLabel, LinearProgress, MenuItem, Select,
  Skeleton, TextField, Typography,
} from '@mui/material';
import ModelTrainingIcon from '@mui/icons-material/ModelTraining';
import DatasetIcon from '@mui/icons-material/Dataset';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import AssessmentIcon from '@mui/icons-material/Assessment';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import DeleteIcon from '@mui/icons-material/Delete';
import IconButton from '@mui/material/IconButton';

import {
  useAssessQuality, useAvailableModels, useCreateFromSource,
  useCreateFTJob, useDeleteFTDataset, useFTDatasets, useFTJobs,
} from '@/features/fine-tuning/hooks/useFineTuning';

const STATUS_COLORS: Record<string, 'default' | 'info' | 'success' | 'error' | 'warning'> = {
  draft: 'default', preparing: 'info', training: 'warning', evaluating: 'info',
  completed: 'success', failed: 'error', ready: 'success', cancelled: 'default',
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
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ModelTrainingIcon color="primary" /> Fine-Tuning Studio
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create datasets from your platform data, train custom AI models, evaluate and deploy
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<DatasetIcon />} onClick={() => setSourceOpen(true)}>
            Create Dataset
          </Button>
          <Button variant="contained" startIcon={<RocketLaunchIcon />} onClick={() => setTrainOpen(true)}
            disabled={!datasets?.some((d) => d.status === 'ready')}>
            Train Model
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Datasets */}
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Training Datasets</Typography>
              {dsLoading ? <Skeleton variant="rectangular" height={200} /> : !datasets?.length ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <DatasetIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                  <Typography color="text.secondary">No datasets yet</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Create one from your transcriptions, conversations, or documents
                  </Typography>
                </Box>
              ) : (
                datasets.map((ds) => (
                  <Card key={ds.id} variant="outlined" sx={{ mb: 1 }}>
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="subtitle2">{ds.name}</Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                          <Chip label={ds.status} size="small" color={STATUS_COLORS[ds.status] || 'default'} />
                          <IconButton size="small" color="error" onClick={() => deleteDsMutation.mutate(ds.id)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Box>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        <Chip label={ds.source_type} size="small" variant="outlined" />
                        <Chip label={`${ds.sample_count} samples`} size="small" variant="outlined" />
                        <Chip label={ds.dataset_type} size="small" variant="outlined" />
                        {ds.quality_score !== null && (
                          <Chip label={`Quality: ${(ds.quality_score * 100).toFixed(0)}%`} size="small"
                            color={ds.quality_score > 0.7 ? 'success' : 'warning'} />
                        )}
                      </Box>
                    </CardContent>
                    <CardActions sx={{ pt: 0 }}>
                      <Button size="small" startIcon={<AssessmentIcon />}
                        onClick={() => assessMutation.mutate(ds.id)}
                        disabled={assessMutation.isPending || ds.status !== 'ready'}>
                        Assess Quality
                      </Button>
                    </CardActions>
                  </Card>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Training Jobs */}
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Training Jobs</Typography>
              {jobsLoading ? <Skeleton variant="rectangular" height={300} /> : !jobs?.length ? (
                <Box sx={{ textAlign: 'center', py: 6 }}>
                  <ModelTrainingIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">No training jobs yet</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Create a dataset first, then start training
                  </Typography>
                </Box>
              ) : (
                jobs.map((job) => {
                  const metrics = JSON.parse(job.metrics_json || '{}');
                  return (
                    <Card key={job.id} variant="outlined" sx={{ mb: 2 }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="subtitle1" fontWeight="bold">{job.name}</Typography>
                          <Chip label={job.status} size="small" color={STATUS_COLORS[job.status] || 'default'} />
                        </Box>
                        <Box sx={{ display: 'flex', gap: 0.5, mb: 1.5 }}>
                          <Chip label={job.base_model} size="small" variant="outlined" />
                          <Chip label={job.provider} size="small" variant="outlined" />
                          <Chip label={`${job.epochs_completed}/${job.total_epochs} epochs`} size="small" variant="outlined" />
                          {job.estimated_cost_usd > 0 && (
                            <Chip label={`~$${job.actual_cost_usd || job.estimated_cost_usd}`} size="small" variant="outlined" />
                          )}
                        </Box>
                        {(job.status === 'training' || job.status === 'preparing') && (
                          <LinearProgress variant="determinate" value={(job.epochs_completed / job.total_epochs) * 100} sx={{ mb: 1 }} />
                        )}
                        {metrics.final_loss !== undefined && (
                          <Typography variant="caption" color="text.secondary">
                            Loss: {metrics.final_loss} | Eval Loss: {metrics.eval_loss}
                          </Typography>
                        )}
                        {job.result_model_id && (
                          <Alert severity="success" sx={{ mt: 1, py: 0 }}>
                            <Typography variant="caption">Model ID: {job.result_model_id}</Typography>
                          </Alert>
                        )}
                        {job.error && <Alert severity="error" sx={{ mt: 1, py: 0 }}>{job.error}</Alert>}
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </CardContent>
          </Card>

          {/* Available Models */}
          {models && (
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 1 }}>Available Base Models</Typography>
                <Grid container spacing={1}>
                  {models.map((m) => (
                    <Grid item xs={6} sm={4} key={m.id}>
                      <Card variant="outlined" sx={{ p: 1 }}>
                        <Typography variant="subtitle2">{m.name}</Typography>
                        <Typography variant="caption" color="text.secondary">{m.parameters} params</Typography>
                        <Box sx={{ display: 'flex', gap: 0.3, mt: 0.5 }}>
                          <Chip label={m.provider} size="small" variant="outlined" />
                          {m.supports_lora && <Chip label="LoRA" size="small" color="success" variant="outlined" />}
                        </Box>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Create Dataset from Source */}
      <Dialog open={sourceOpen} onClose={() => setSourceOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Dataset from Platform Data</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Dataset Name" value={sourceName}
            onChange={(e) => setSourceName(e.target.value)} sx={{ mt: 1, mb: 2 }} />
          <Typography variant="subtitle2" sx={{ mb: 1 }}>Data Source</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
            {SOURCE_OPTIONS.map((s) => (
              <Chip key={s.id} label={`${s.icon} ${s.label}`}
                variant={sourceType === s.id ? 'filled' : 'outlined'}
                color={sourceType === s.id ? 'primary' : 'default'}
                onClick={() => setSourceType(s.id)} />
            ))}
          </Box>
          <TextField fullWidth size="small" type="number" label="Max Samples"
            value={maxSamples} onChange={(e) => setMaxSamples(Number(e.target.value))} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSourceOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateFromSource}
            disabled={!sourceName.trim() || createFromSourceMutation.isPending}
            startIcon={createFromSourceMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <AutoAwesomeIcon />}>
            Create Dataset
          </Button>
        </DialogActions>
      </Dialog>

      {/* Train Model */}
      <Dialog open={trainOpen} onClose={() => setTrainOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Train Custom Model</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Model Name" value={trainName}
            onChange={(e) => setTrainName(e.target.value)} sx={{ mt: 1, mb: 2 }} />
          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
            <InputLabel>Dataset</InputLabel>
            <Select value={trainDataset} label="Dataset" onChange={(e) => setTrainDataset(e.target.value)}>
              {datasets?.filter((d) => d.status === 'ready').map((d) => (
                <MenuItem key={d.id} value={d.id}>{d.name} ({d.sample_count} samples)</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
            <InputLabel>Base Model</InputLabel>
            <Select value={trainModel} label="Base Model" onChange={(e) => setTrainModel(e.target.value)}>
              {models?.map((m) => (
                <MenuItem key={m.id} value={m.id}>{m.name} ({m.parameters})</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField fullWidth size="small" type="number" label="Epochs"
            value={trainEpochs} onChange={(e) => setTrainEpochs(Number(e.target.value))}
            inputProps={{ min: 1, max: 10 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTrainOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleTrain}
            disabled={!trainName.trim() || !trainDataset || createJobMutation.isPending}
            startIcon={createJobMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <RocketLaunchIcon />}>
            Start Training
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
