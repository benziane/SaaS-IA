'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Skeleton,
  TextField,
  Typography,
} from '@mui/material';

import { useAgentRuns, useRunAgent } from '@/features/agents/hooks/useAgents';
import type { AgentRun } from '@/features/agents/types';

const STATUS_COLORS: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
  planning: 'default',
  executing: 'primary',
  completed: 'success',
  failed: 'error',
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
};

function RunCard({ run }: { run: AgentRun }) {
  const progress = run.total_steps > 0 ? (run.current_step / run.total_steps) * 100 : 0;

  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }} noWrap>
            {run.instruction.substring(0, 80)}{run.instruction.length > 80 ? '...' : ''}
          </Typography>
          <Chip label={run.status} size="small" color={STATUS_COLORS[run.status] || 'default'} />
        </Box>

        {run.status === 'executing' && (
          <LinearProgress variant="determinate" value={progress} sx={{ mb: 1, height: 6, borderRadius: 3 }} />
        )}

        <Typography variant="caption" color="text.secondary">
          {run.total_steps} steps | {new Date(run.created_at).toLocaleString()}
        </Typography>

        {run.steps.length > 0 && (
          <List dense sx={{ mt: 1 }}>
            {run.steps.map((step) => (
              <ListItem key={step.id} sx={{ py: 0 }}>
                <ListItemText
                  primary={`${step.step_index + 1}. ${ACTION_LABELS[step.action] || step.action}`}
                  secondary={step.description}
                  primaryTypographyProps={{ variant: 'body2' }}
                  secondaryTypographyProps={{ variant: 'caption' }}
                />
                <Chip label={step.status} size="small" color={STATUS_COLORS[step.status] || 'default'} variant="outlined" />
              </ListItem>
            ))}
          </List>
        )}

        {run.error && (
          <Alert severity="error" sx={{ mt: 1 }}>{run.error}</Alert>
        )}
      </CardContent>
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
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>AI Agents</Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>New Agent Task</Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="Describe what you want the agent to do..."
            sx={{ mb: 2 }}
          />
          <Button
            variant="contained"
            onClick={handleRun}
            disabled={!instruction.trim() || runMutation.isPending}
          >
            {runMutation.isPending ? <><CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />Running...</> : 'Run Agent'}
          </Button>

          {runMutation.isError && (
            <Alert severity="error" sx={{ mt: 2 }}>{runMutation.error?.message}</Alert>
          )}
        </CardContent>
      </Card>

      {runMutation.data && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Latest Result</Typography>
          <RunCard run={runMutation.data} />
        </Box>
      )}

      <Typography variant="h6" sx={{ mb: 2 }}>History</Typography>
      {isLoading ? (
        <Skeleton variant="rectangular" height={200} />
      ) : !runs?.length ? (
        <Typography variant="body2" color="text.secondary">No agent runs yet.</Typography>
      ) : (
        runs.map((run) => <RunCard key={run.id} run={run} />)
      )}
    </Box>
  );
}
