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
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Skeleton,
  TextField,
  Typography,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

import { useAgentRuns, useRunAgent } from '@/features/agents/hooks/useAgents';
import type { AgentRun, AgentStep } from '@/features/agents/types';

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
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h6">{ACTION_LABELS[step.action] || step.action}</Typography>
          <Typography variant="caption" color="text.secondary">{step.description}</Typography>
        </Box>
        <IconButton onClick={onClose} size="small"><CloseIcon /></IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ maxHeight: '70vh', overflowY: 'auto' }}>
        <Typography
          variant="body2"
          sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: 'monospace', fontSize: '0.82rem' }}
        >
          {output || 'Pas de résultat disponible.'}
        </Typography>
      </DialogContent>
    </Dialog>
  );
}

function RunCard({ run }: { run: AgentRun }) {
  const [selectedStep, setSelectedStep] = useState<AgentStep | null>(null);
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
                <ListItem key={step.id} sx={{ py: 0, flexDirection: 'column', alignItems: 'stretch' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <ListItemText
                      primary={`${step.step_index + 1}. ${ACTION_LABELS[step.action] || step.action}`}
                      secondary={step.description}
                      primaryTypographyProps={{ variant: 'body2' }}
                      secondaryTypographyProps={{ variant: 'caption' }}
                    />
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      {stepOutput && (
                        <Button size="small" variant="text" onClick={() => setSelectedStep(step)} sx={{ minWidth: 0, fontSize: '0.7rem' }}>
                          Voir
                        </Button>
                      )}
                      <Chip label={step.status} size="small" color={STATUS_COLORS[step.status] || 'default'} variant="outlined" />
                    </Box>
                  </Box>
                  {stepOutput && (
                    <Typography
                      variant="caption"
                      sx={{
                        mt: 0.5,
                        mb: 1,
                        p: 1,
                        bgcolor: 'action.hover',
                        borderRadius: 1,
                        whiteSpace: 'pre-wrap',
                        maxHeight: 80,
                        overflow: 'hidden',
                        display: 'block',
                        cursor: 'pointer',
                      }}
                      onClick={() => setSelectedStep(step)}
                    >
                      {stepOutput.substring(0, 200)}{stepOutput.length > 200 ? '… (cliquer pour voir tout)' : ''}
                    </Typography>
                  )}
                </ListItem>
              );
            })}
          </List>
        )}

        {run.error && (
          <Alert severity="error" sx={{ mt: 1 }}>{run.error}</Alert>
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
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ width: '100%' }}>Try:</Typography>
            {[
              'Summarize my latest transcription',
              'Search knowledge base for meeting notes',
              'Analyze sentiment of a text about customer feedback',
              'Compare AI models on: explain quantum computing',
            ].map((suggestion) => (
              <Chip
                key={suggestion}
                label={suggestion}
                size="small"
                variant="outlined"
                onClick={() => setInstruction(suggestion)}
                sx={{ cursor: 'pointer' }}
              />
            ))}
          </Box>
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
