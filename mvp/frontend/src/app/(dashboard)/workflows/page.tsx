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
  IconButton,
  LinearProgress,
  Skeleton,
  Step,
  StepLabel,
  Stepper,
  TextField,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DeleteIcon from '@mui/icons-material/Delete';
import HistoryIcon from '@mui/icons-material/History';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

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

const STATUS_COLORS: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning' | 'info'> = {
  draft: 'default',
  active: 'primary',
  paused: 'warning',
  archived: 'default',
  pending: 'default',
  running: 'info',
  completed: 'success',
  failed: 'error',
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
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AccountTreeIcon color="primary" /> AI Workflows
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Build no-code AI automation workflows with triggers, actions, and templates
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<AutoFixHighIcon />} onClick={() => setTemplatesOpen(true)}>
            Templates
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
            New Workflow
          </Button>
        </Box>
      </Box>

      {/* Templates Section */}
      {templates && templates.length > 0 && !workflows?.length && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>Quick Start with Templates</Typography>
          <Grid container spacing={2}>
            {templates.slice(0, 3).map((template) => (
              <Grid item xs={12} sm={4} key={template.id}>
                <Card
                  variant="outlined"
                  sx={{ cursor: 'pointer', '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' } }}
                  onClick={() => handleUseTemplate(template.id)}
                >
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight="bold">{template.name}</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 1 }}>
                      {template.description}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Chip label={template.category} size="small" color="primary" variant="outlined" />
                      <Chip label={`${template.nodes.length} steps`} size="small" variant="outlined" />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Workflows Grid */}
      {isLoading ? (
        <Grid container spacing={3}>
          {[1, 2, 3].map((i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rectangular" height={220} sx={{ borderRadius: 1 }} />
            </Grid>
          ))}
        </Grid>
      ) : !workflows?.length ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <AccountTreeIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">No workflows yet</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
              Create a workflow from scratch or use a template to get started
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
              <Button variant="outlined" onClick={() => setTemplatesOpen(true)}>Browse Templates</Button>
              <Button variant="contained" onClick={() => setCreateOpen(true)}>Create Blank</Button>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {workflows.map((workflow) => (
            <Grid item xs={12} sm={6} md={4} key={workflow.id}>
              <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="subtitle1" fontWeight="bold" noWrap>
                      {workflow.name}
                    </Typography>
                    <Chip
                      label={workflow.status}
                      size="small"
                      color={STATUS_COLORS[workflow.status] || 'default'}
                    />
                  </Box>
                  {workflow.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5, overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                      {workflow.description}
                    </Typography>
                  )}

                  {/* Node flow preview */}
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1.5 }}>
                    {workflow.nodes.map((node, i) => (
                      <Box key={node.id} sx={{ display: 'flex', alignItems: 'center', gap: 0.3 }}>
                        <Chip
                          label={`${ACTION_ICONS[node.action] || '⚙️'} ${node.label || node.action}`}
                          size="small"
                          variant="outlined"
                        />
                        {i < workflow.nodes.length - 1 && (
                          <Typography variant="caption" color="text.disabled">→</Typography>
                        )}
                      </Box>
                    ))}
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip label={TRIGGER_LABELS[workflow.trigger_type] || workflow.trigger_type} size="small" variant="outlined" />
                    <Chip label={`${workflow.run_count} runs`} size="small" variant="outlined" />
                    {workflow.template_category && (
                      <Chip label={workflow.template_category} size="small" color="primary" variant="outlined" />
                    )}
                  </Box>
                </CardContent>
                <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                  <Box>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => deleteMutation.mutate(workflow.id)}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => setSelectedWorkflow(
                        selectedWorkflow === workflow.id ? null : workflow.id
                      )}
                    >
                      <HistoryIcon fontSize="small" />
                    </IconButton>
                  </Box>
                  <Button
                    variant="contained"
                    size="small"
                    startIcon={triggerMutation.isPending ? <CircularProgress size={14} color="inherit" /> : <PlayArrowIcon />}
                    onClick={() => handleTrigger(workflow.id)}
                    disabled={triggerMutation.isPending || workflow.nodes.length === 0}
                  >
                    Run
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Run History Panel */}
      {selectedWorkflow && runs && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Run History</Typography>
            {runs.length === 0 ? (
              <Typography color="text.secondary">No runs yet</Typography>
            ) : (
              runs.map((run) => (
                <Card key={run.id} variant="outlined" sx={{ mb: 1, cursor: 'pointer' }} onClick={() => setRunResult(run)}>
                  <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip label={run.status} size="small" color={STATUS_COLORS[run.status] || 'default'} />
                        <Typography variant="body2">
                          {run.current_node}/{run.total_nodes} nodes
                        </Typography>
                        {run.duration_ms && (
                          <Typography variant="caption" color="text.secondary">
                            {(run.duration_ms / 1000).toFixed(1)}s
                          </Typography>
                        )}
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(run.created_at).toLocaleString()}
                      </Typography>
                    </Box>
                    {run.status === 'running' && (
                      <LinearProgress sx={{ mt: 1 }} variant="determinate" value={(run.current_node / run.total_nodes) * 100} />
                    )}
                    {run.error && (
                      <Alert severity="error" sx={{ mt: 1, py: 0 }}>{run.error}</Alert>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {/* Run Input Dialog */}
      <Dialog open={runOpen} onClose={() => setRunOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Run Workflow</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Optionally provide input text/data for the first node of the workflow.
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Input Text (optional)"
            placeholder="Enter text, URL, or data to process..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRunOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleRunConfirm}
            startIcon={triggerMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <PlayArrowIcon />}
            disabled={triggerMutation.isPending}
          >
            Run Now
          </Button>
        </DialogActions>
      </Dialog>

      {/* Run Result Dialog */}
      <Dialog open={!!runResult} onClose={() => setRunResult(null)} maxWidth="md" fullWidth>
        {runResult && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="h6">Workflow Run</Typography>
                <Chip label={runResult.status} size="small" color={STATUS_COLORS[runResult.status] || 'default'} />
                {runResult.duration_ms && (
                  <Chip label={`${(runResult.duration_ms / 1000).toFixed(1)}s`} size="small" variant="outlined" />
                )}
              </Box>
            </DialogTitle>
            <DialogContent dividers>
              {runResult.results.length > 0 ? (
                <Stepper orientation="vertical" activeStep={runResult.results.length}>
                  {runResult.results.map((result: Record<string, unknown>, i: number) => (
                    <Step key={i} completed>
                      <StepLabel>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle2">
                            {ACTION_ICONS[(result.action as string) || ''] || '⚙️'}{' '}
                            {(result.label as string) || (result.action as string) || `Step ${i + 1}`}
                          </Typography>
                          {Boolean(result.error) && <Chip label="error" size="small" color="error" />}
                        </Box>
                      </StepLabel>
                      <Box sx={{ ml: 4, mb: 2 }}>
                        {Boolean(result.output) && (
                          <Box sx={{ position: 'relative' }}>
                            <Box
                              sx={{
                                p: 1.5,
                                bgcolor: 'action.hover',
                                borderRadius: 1,
                                fontSize: '0.85rem',
                                whiteSpace: 'pre-wrap',
                                maxHeight: 200,
                                overflow: 'auto',
                                wordBreak: 'break-word',
                              }}
                            >
                              {(result.output as string).substring(0, 1000)}
                              {(result.output as string).length > 1000 && '...'}
                            </Box>
                            <IconButton
                              size="small"
                              sx={{ position: 'absolute', top: 4, right: 4 }}
                              onClick={() => navigator.clipboard.writeText(result.output as string)}
                            >
                              <ContentCopyIcon fontSize="small" />
                            </IconButton>
                          </Box>
                        )}
                        {Boolean(result.error) && (
                          <Alert severity="error" sx={{ mt: 1 }}>{result.error as string}</Alert>
                        )}
                      </Box>
                    </Step>
                  ))}
                </Stepper>
              ) : (
                <Typography color="text.secondary">No results yet</Typography>
              )}
              {runResult.error && (
                <Alert severity="error" sx={{ mt: 2 }}>{runResult.error}</Alert>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setRunResult(null)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Templates Dialog */}
      <Dialog open={templatesOpen} onClose={() => setTemplatesOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Workflow Templates</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0 }}>
            {templates?.map((template) => (
              <Grid item xs={12} sm={6} key={template.id}>
                <Card
                  variant="outlined"
                  sx={{ cursor: 'pointer', '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' } }}
                  onClick={() => handleUseTemplate(template.id)}
                >
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight="bold">{template.name}</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 1.5 }}>
                      {template.description}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
                      {template.nodes.map((node, i) => (
                        <Box key={node.id} sx={{ display: 'flex', alignItems: 'center', gap: 0.3 }}>
                          <Chip
                            label={`${ACTION_ICONS[node.action] || '⚙️'} ${node.label}`}
                            size="small"
                            variant="outlined"
                          />
                          {i < template.nodes.length - 1 && (
                            <Typography variant="caption" color="text.disabled">→</Typography>
                          )}
                        </Box>
                      ))}
                    </Box>
                    <Chip label={template.category} size="small" color="primary" variant="outlined" />
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
          {createFromTemplateMutation.isPending && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <CircularProgress />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTemplatesOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Create Blank Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Workflow</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Workflow Name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            fullWidth
            multiline
            rows={2}
            label="Description (optional)"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateBlank}
            disabled={!newName.trim() || createMutation.isPending}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {triggerMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>{triggerMutation.error?.message}</Alert>
      )}
    </Box>
  );
}
