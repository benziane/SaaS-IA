'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Skeleton,
  TextField,
  Typography,
} from '@mui/material';

import {
  useCreatePipeline,
  useDeletePipeline,
  useExecutePipeline,
  usePipelines,
} from '@/features/pipelines/hooks/usePipelines';
import type { PipelineExecution } from '@/features/pipelines/types';

const STATUS_COLORS: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
  draft: 'default',
  active: 'primary',
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
      <Box sx={{ p: 3 }}>
        <Skeleton variant="text" width={200} height={40} sx={{ mb: 2 }} />
        <Grid container spacing={3}>
          {[1, 2, 3].map((i) => (
            <Grid item xs={12} md={4} key={i}>
              <Skeleton variant="rectangular" height={180} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Failed to load pipelines.</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">AI Pipelines</Typography>
        <Button variant="contained" onClick={() => setCreateOpen(true)}>
          Create Pipeline
        </Button>
      </Box>

      {execResult && (
        <Alert
          severity={execResult.status === 'completed' ? 'success' : execResult.status === 'failed' ? 'error' : 'info'}
          sx={{ mb: 3 }}
          onClose={() => setExecResult(null)}
        >
          Pipeline execution {execResult.status}.
          {execResult.error && ` Error: ${execResult.error}`}
          {execResult.status === 'completed' && ` (${execResult.total_steps} steps completed)`}
        </Alert>
      )}

      {!pipelines?.length ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
              No pipelines yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Create your first AI pipeline to chain operations like transcription, summarization, and translation.
            </Typography>
            <Button variant="outlined" onClick={() => setCreateOpen(true)}>
              Create Pipeline
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {pipelines.map((pipeline) => (
            <Grid item xs={12} md={4} key={pipeline.id}>
              <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="h6" noWrap>
                      {pipeline.name}
                    </Typography>
                    <Chip
                      label={pipeline.status}
                      size="small"
                      color={STATUS_COLORS[pipeline.status] || 'default'}
                    />
                  </Box>
                  {pipeline.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {pipeline.description}
                    </Typography>
                  )}
                  <Typography variant="caption" color="text.secondary">
                    {pipeline.steps.length} steps
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    {pipeline.steps.map((step) => (
                      <Chip
                        key={step.id}
                        label={step.type}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))}
                  </Box>
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    onClick={() => handleExecute(pipeline.id)}
                    disabled={executeMutation.isPending}
                  >
                    {executeMutation.isPending ? <CircularProgress size={16} /> : 'Execute'}
                  </Button>
                  <Button
                    size="small"
                    color="error"
                    onClick={() => deleteMutation.mutate(pipeline.id)}
                    disabled={deleteMutation.isPending}
                  >
                    Delete
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Pipeline Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Pipeline</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Pipeline Name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            fullWidth
            label="Description (optional)"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            multiline
            rows={2}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            A default pipeline with Transcription and Summarize steps will be created.
            You can edit the steps later.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!newName.trim() || createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
