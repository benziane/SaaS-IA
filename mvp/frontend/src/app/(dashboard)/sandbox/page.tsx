'use client';

import { useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  Dialog, DialogActions, DialogContent, DialogTitle,
  Divider, Grid, IconButton, Skeleton, TextField, Typography,
} from '@mui/material';
import CodeIcon from '@mui/icons-material/Code';
import AddIcon from '@mui/icons-material/Add';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DeleteIcon from '@mui/icons-material/Delete';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import BugReportIcon from '@mui/icons-material/BugReport';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import SmartToyIcon from '@mui/icons-material/SmartToy';

import {
  useAddCell, useCreateSandbox, useDeleteCell, useDeleteSandbox,
  useExecuteCell, useExplainCode, useGenerateCode, useDebugCode,
  useSandbox, useSandboxes, useUpdateCell,
} from '@/features/code-sandbox/hooks/useCodeSandbox';
import type { SandboxCell } from '@/features/code-sandbox/types';

const STATUS_COLORS: Record<string, 'default' | 'info' | 'success' | 'error' | 'warning'> = {
  idle: 'default', running: 'info', success: 'success', error: 'error', timeout: 'warning',
  active: 'success', archived: 'default',
};

export default function SandboxPage() {
  const { data: sandboxes, isLoading } = useSandboxes();
  const createMutation = useCreateSandbox();
  const deleteSandboxMutation = useDeleteSandbox();

  const [activeSandboxId, setActiveSandboxId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [generatePrompt, setGeneratePrompt] = useState('');

  const { data: activeSandbox } = useSandbox(activeSandboxId);
  const addCellMutation = useAddCell(activeSandboxId || '');
  const executeCellMutation = useExecuteCell(activeSandboxId || '');
  const deleteCellMutation = useDeleteCell(activeSandboxId || '');
  const updateCellMutation = useUpdateCell(activeSandboxId || '');
  const generateMutation = useGenerateCode();
  const explainMutation = useExplainCode();
  const debugMutation = useDebugCode();

  const [editingSources, setEditingSources] = useState<Record<string, string>>({});

  const handleCreate = () => {
    if (!newName.trim()) return;
    createMutation.mutate(
      { name: newName, description: newDesc || undefined },
      { onSuccess: (s) => { setActiveSandboxId(s.id); setCreateOpen(false); setNewName(''); setNewDesc(''); } },
    );
  };

  const handleAddCell = () => {
    addCellMutation.mutate({ source: '# Write your code here\n', cell_type: 'code' });
  };

  const handleExecute = (cellId: string) => {
    // Save pending edits before executing
    const pendingSource = editingSources[cellId];
    if (pendingSource !== undefined) {
      updateCellMutation.mutate(
        { cellId, source: pendingSource },
        { onSuccess: () => { executeCellMutation.mutate(cellId); } },
      );
    } else {
      executeCellMutation.mutate(cellId);
    }
  };

  const handleGenerate = () => {
    if (!generatePrompt.trim()) return;
    generateMutation.mutate(
      { prompt: generatePrompt },
      {
        onSuccess: (res) => {
          addCellMutation.mutate({ source: res.code, cell_type: 'code' });
          setGeneratePrompt('');
        },
      },
    );
  };

  const handleExplain = (code: string) => {
    explainMutation.mutate(code);
  };

  const handleDebug = (cell: SandboxCell) => {
    if (cell.error) {
      debugMutation.mutate(
        { code: cell.source, error: cell.error },
        {
          onSuccess: (res) => {
            addCellMutation.mutate({ source: res.fixed_code, cell_type: 'code' });
          },
        },
      );
    }
  };

  const getCellSource = (cell: SandboxCell) => editingSources[cell.id] ?? cell.source;

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CodeIcon color="primary" /> Code Sandbox
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Write, execute, and debug code in a secure sandbox with AI assistance
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Sandbox list */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Sandboxes</Typography>
                <Button size="small" variant="outlined" startIcon={<AddIcon />}
                  onClick={() => setCreateOpen(true)}>New</Button>
              </Box>

              {isLoading ? <Skeleton variant="rectangular" height={200} /> : !sandboxes?.length ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <CodeIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                  <Typography color="text.secondary">Create your first sandbox</Typography>
                </Box>
              ) : (
                sandboxes.map((s) => (
                  <Card key={s.id} variant="outlined" sx={{
                    mb: 1, cursor: 'pointer',
                    bgcolor: activeSandboxId === s.id ? 'action.selected' : 'transparent',
                    '&:hover': { bgcolor: 'action.hover' },
                  }} onClick={() => { setActiveSandboxId(s.id); setEditingSources({}); }}>
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="subtitle2" noWrap>{s.name}</Typography>
                        <IconButton size="small" color="error" onClick={(e) => {
                          e.stopPropagation();
                          deleteSandboxMutation.mutate(s.id);
                          if (activeSandboxId === s.id) setActiveSandboxId(null);
                        }}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                        <Chip label={s.language} size="small" variant="outlined" />
                        <Chip label={`${s.cells.length} cells`} size="small" variant="outlined" />
                        <Chip label={s.status} size="small" color={STATUS_COLORS[s.status] || 'default'} />
                      </Box>
                    </CardContent>
                  </Card>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Editor & output */}
        <Grid item xs={12} md={9}>
          {activeSandbox ? (
            <Box>
              {/* AI generate bar */}
              <Card sx={{ mb: 2 }}>
                <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <SmartToyIcon color="primary" />
                    <TextField fullWidth size="small" placeholder="Describe what code you want to generate..."
                      value={generatePrompt} onChange={(e) => setGeneratePrompt(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') handleGenerate(); }} />
                    <Button variant="contained" size="small" startIcon={
                      generateMutation.isPending ? <CircularProgress size={14} /> : <AutoFixHighIcon />
                    } onClick={handleGenerate} disabled={!generatePrompt.trim() || generateMutation.isPending}>
                      Generate
                    </Button>
                  </Box>
                </CardContent>
              </Card>

              {/* Cells */}
              {activeSandbox.cells.map((cell, idx) => (
                <Card key={cell.id} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip label={`[${idx + 1}]`} size="small" color="primary" variant="outlined" />
                        <Chip label={cell.language} size="small" variant="outlined" />
                        {cell.status !== 'idle' && (
                          <Chip label={cell.status} size="small" color={STATUS_COLORS[cell.status] || 'default'} />
                        )}
                        {cell.execution_time_ms != null && (
                          <Typography variant="caption" color="text.secondary">
                            {cell.execution_time_ms.toFixed(0)}ms
                          </Typography>
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <IconButton size="small" color="success" title="Run cell"
                          onClick={() => handleExecute(cell.id)}
                          disabled={executeCellMutation.isPending}>
                          {executeCellMutation.isPending && executeCellMutation.variables === cell.id
                            ? <CircularProgress size={16} /> : <PlayArrowIcon fontSize="small" />}
                        </IconButton>
                        <IconButton size="small" title="Explain code"
                          onClick={() => handleExplain(getCellSource(cell))}
                          disabled={explainMutation.isPending}>
                          <LightbulbIcon fontSize="small" />
                        </IconButton>
                        {cell.error && (
                          <IconButton size="small" color="warning" title="Debug with AI"
                            onClick={() => handleDebug(cell)}
                            disabled={debugMutation.isPending}>
                            <BugReportIcon fontSize="small" />
                          </IconButton>
                        )}
                        <IconButton size="small" color="error" title="Delete cell"
                          onClick={() => deleteCellMutation.mutate(cell.id)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </Box>

                    {/* Code editor */}
                    <TextField
                      fullWidth multiline minRows={3} maxRows={20}
                      value={getCellSource(cell)}
                      onChange={(e) => setEditingSources((prev) => ({ ...prev, [cell.id]: e.target.value }))}
                      onBlur={() => {
                        const src = editingSources[cell.id];
                        if (src !== undefined && src !== cell.source) {
                          updateCellMutation.mutate({ cellId: cell.id, source: src });
                        }
                      }}
                      sx={{
                        fontFamily: 'monospace',
                        '& .MuiInputBase-input': { fontFamily: '"Fira Code", "Consolas", monospace', fontSize: '0.875rem' },
                        bgcolor: 'grey.50',
                      }}
                    />

                    {/* Output */}
                    {cell.output && (
                      <Box sx={{ mt: 1, p: 1.5, bgcolor: 'grey.900', borderRadius: 1, maxHeight: 300, overflow: 'auto' }}>
                        <Typography variant="body2" component="pre" sx={{
                          fontFamily: 'monospace', fontSize: '0.8rem', color: '#4caf50', whiteSpace: 'pre-wrap', m: 0,
                        }}>
                          {cell.output}
                        </Typography>
                      </Box>
                    )}

                    {/* Error */}
                    {cell.error && (
                      <Alert severity="error" sx={{ mt: 1, fontFamily: 'monospace', fontSize: '0.8rem' }}>
                        {cell.error}
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              ))}

              {/* Add cell button */}
              <Box sx={{ textAlign: 'center', py: 2 }}>
                <Button variant="outlined" startIcon={<AddIcon />} onClick={handleAddCell}>
                  Add Cell
                </Button>
              </Box>

              {/* AI explanation panel */}
              {explainMutation.data && (
                <Card sx={{ mt: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                      <LightbulbIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'text-bottom' }} />
                      AI Explanation
                    </Typography>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {explainMutation.data.explanation}
                    </Typography>
                    {explainMutation.data.complexity && (
                      <Chip label={`Complexity: ${explainMutation.data.complexity}`} size="small" sx={{ mt: 1 }} />
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Debug result panel */}
              {debugMutation.data && (
                <Card sx={{ mt: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle2" color="warning.main" sx={{ mb: 1 }}>
                      <BugReportIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'text-bottom' }} />
                      Debug Result
                    </Typography>
                    <Alert severity="info" sx={{ mb: 1 }}>Root cause: {debugMutation.data.root_cause}</Alert>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>
                      {debugMutation.data.explanation}
                    </Typography>
                  </CardContent>
                </Card>
              )}
            </Box>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <CodeIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">Select or create a sandbox to start coding</Typography>
                <Typography variant="body2" color="text.secondary">
                  Write code, run it in a secure environment, and use AI to generate, explain, or debug
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Create dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Sandbox</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Name" value={newName} onChange={(e) => setNewName(e.target.value)}
            sx={{ mt: 1, mb: 2 }} autoFocus />
          <TextField fullWidth label="Description (optional)" value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)} multiline rows={2} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={!newName.trim() || createMutation.isPending}>
            {createMutation.isPending ? <CircularProgress size={20} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
