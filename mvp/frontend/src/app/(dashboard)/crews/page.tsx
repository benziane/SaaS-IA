'use client';

import { useState } from 'react';
import {
  Alert, Avatar, Box, Button, Card, CardActions, CardContent, Chip,
  CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle,
  Divider, Grid, IconButton, Skeleton, Step, StepLabel, Stepper,
  TextField, Typography,
} from '@mui/material';
import GroupsIcon from '@mui/icons-material/Groups';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

import {
  useCreateFromTemplate, useCrewTemplates, useCrews,
  useDeleteCrew, useRunCrew,
} from '@/features/crews/hooks/useCrews';
import type { CrewRun } from '@/features/crews/types';

const ROLE_ICONS: Record<string, string> = {
  researcher: '🔬', writer: '✍️', reviewer: '📝', analyst: '📊',
  coder: '💻', translator: '🌐', summarizer: '📋', creative: '🎨', custom: '⚙️',
};

const STATUS_COLORS: Record<string, 'default' | 'primary' | 'success' | 'error' | 'info'> = {
  draft: 'default', active: 'primary', pending: 'default',
  running: 'info', completed: 'success', failed: 'error',
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
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <GroupsIcon color="primary" /> AI Agent Crews
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Build collaborative teams of specialized AI agents
          </Typography>
        </Box>
        <Button variant="outlined" startIcon={<AutoFixHighIcon />} onClick={() => setTemplatesOpen(true)}>
          Templates
        </Button>
      </Box>

      {/* Templates quick start */}
      {!crews?.length && templates && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {templates.map((t) => (
            <Grid item xs={12} sm={6} md={3} key={t.id}>
              <Card variant="outlined" sx={{ cursor: 'pointer', '&:hover': { borderColor: 'primary.main' } }}
                onClick={() => templateMutation.mutate({ templateId: t.id })}>
                <CardContent>
                  <Typography variant="subtitle2" fontWeight="bold">{t.name}</Typography>
                  <Typography variant="caption" color="text.secondary">{t.description}</Typography>
                  <Box sx={{ mt: 1, display: 'flex', gap: 0.5 }}>
                    {t.agents.map((a) => (
                      <Chip key={a.id} label={`${ROLE_ICONS[a.role] || '⚙️'} ${a.name}`} size="small" variant="outlined" />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {isLoading ? (
        <Skeleton variant="rectangular" height={300} />
      ) : !crews?.length ? (
        <Card><CardContent sx={{ textAlign: 'center', py: 8 }}>
          <GroupsIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">No crews yet</Typography>
          <Button onClick={() => setTemplatesOpen(true)} sx={{ mt: 1 }}>Use a Template</Button>
        </CardContent></Card>
      ) : (
        <Grid container spacing={3}>
          {crews.map((crew) => (
            <Grid item xs={12} sm={6} md={4} key={crew.id}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="subtitle1" fontWeight="bold">{crew.name}</Typography>
                    <Chip label={crew.status} size="small" color={STATUS_COLORS[crew.status] || 'default'} />
                  </Box>
                  {crew.goal && <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{crew.goal}</Typography>}
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
                    {crew.agents.map((a) => (
                      <Chip key={a.id} label={`${ROLE_ICONS[a.role] || '⚙️'} ${a.name}`} size="small" variant="outlined" />
                    ))}
                  </Box>
                  <Chip label={`${crew.process_type} | ${crew.run_count} runs`} size="small" variant="outlined" />
                </CardContent>
                <CardActions sx={{ justifyContent: 'space-between' }}>
                  <IconButton size="small" color="error" onClick={() => deleteMutation.mutate(crew.id)}><DeleteIcon fontSize="small" /></IconButton>
                  <Button size="small" variant="contained" startIcon={<PlayArrowIcon />}
                    onClick={() => { setRunCrewId(crew.id); setInstruction(''); setRunOpen(true); }}>
                    Run
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Run Dialog */}
      <Dialog open={runOpen} onClose={() => setRunOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Run Agent Crew</DialogTitle>
        <DialogContent>
          <TextField fullWidth multiline rows={4} label="Instruction" placeholder="What should the crew accomplish?"
            value={instruction} onChange={(e) => setInstruction(e.target.value)} sx={{ mt: 1 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRunOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleRun} disabled={!instruction.trim() || runMutation.isPending}
            startIcon={runMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <PlayArrowIcon />}>
            Run Crew
          </Button>
        </DialogActions>
      </Dialog>

      {/* Result Dialog */}
      <Dialog open={!!runResult} onClose={() => setRunResult(null)} maxWidth="md" fullWidth>
        {runResult && (<>
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              Crew Run <Chip label={runResult.status} size="small" color={STATUS_COLORS[runResult.status] || 'default'} />
              {runResult.duration_ms && <Chip label={`${(runResult.duration_ms / 1000).toFixed(1)}s`} size="small" variant="outlined" />}
            </Box>
          </DialogTitle>
          <DialogContent dividers>
            <Stepper orientation="vertical" activeStep={runResult.messages.length}>
              {runResult.messages.map((msg, i) => (
                <Step key={i} completed>
                  <StepLabel>
                    <Typography variant="subtitle2">{ROLE_ICONS[msg.role] || '⚙️'} {msg.agent_name} ({msg.role})</Typography>
                    {msg.tool_used && <Chip label={`tool: ${msg.tool_used}`} size="small" sx={{ ml: 1 }} />}
                  </StepLabel>
                  <Box sx={{ ml: 4, mb: 2, p: 1.5, bgcolor: 'action.hover', borderRadius: 1, fontSize: '0.85rem', whiteSpace: 'pre-wrap', maxHeight: 200, overflow: 'auto', position: 'relative' }}>
                    {msg.content.substring(0, 1500)}{msg.content.length > 1500 && '...'}
                    <IconButton size="small" sx={{ position: 'absolute', top: 4, right: 4 }}
                      onClick={() => navigator.clipboard.writeText(msg.content)}><ContentCopyIcon fontSize="small" /></IconButton>
                  </Box>
                </Step>
              ))}
            </Stepper>
            {runResult.final_output && (<>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Final Output</Typography>
              <Box sx={{ p: 2, bgcolor: 'success.50', borderRadius: 1, whiteSpace: 'pre-wrap' }}>{runResult.final_output}</Box>
            </>)}
            {runResult.error && <Alert severity="error" sx={{ mt: 2 }}>{runResult.error}</Alert>}
          </DialogContent>
          <DialogActions><Button onClick={() => setRunResult(null)}>Close</Button></DialogActions>
        </>)}
      </Dialog>

      {/* Templates Dialog */}
      <Dialog open={templatesOpen} onClose={() => setTemplatesOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Crew Templates</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0 }}>
            {templates?.map((t) => (
              <Grid item xs={12} sm={6} key={t.id}>
                <Card variant="outlined" sx={{ cursor: 'pointer', '&:hover': { borderColor: 'primary.main' } }}
                  onClick={() => { templateMutation.mutate({ templateId: t.id }); setTemplatesOpen(false); }}>
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight="bold">{t.name}</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{t.description}</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {t.agents.map((a) => (
                        <Chip key={a.id} label={`${ROLE_ICONS[a.role] || '⚙️'} ${a.name}`} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions><Button onClick={() => setTemplatesOpen(false)}>Close</Button></DialogActions>
      </Dialog>
    </Box>
  );
}
