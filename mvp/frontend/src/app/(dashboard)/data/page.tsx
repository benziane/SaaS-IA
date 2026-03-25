'use client';

import { useRef, useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  Divider, Grid, IconButton, Skeleton, TextField, Typography,
} from '@mui/material';
import BarChartIcon from '@mui/icons-material/BarChart';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import DeleteIcon from '@mui/icons-material/Delete';
import SendIcon from '@mui/icons-material/Send';

import {
  useAnalyses, useAskData, useAutoAnalyze, useDatasets, useDeleteDataset, useUploadDataset,
} from '@/features/data-analyst/hooks/useDataAnalyst';

const STATUS_COLORS: Record<string, 'default' | 'info' | 'success' | 'error'> = {
  uploading: 'default', processing: 'info', ready: 'success', failed: 'error',
  pending: 'default', analyzing: 'info', completed: 'success',
};

export default function DataPage() {
  const { data: datasets, isLoading } = useDatasets();
  const uploadMutation = useUploadDataset();
  const deleteMutation = useDeleteDataset();

  const [activeDataset, setActiveDataset] = useState<string | null>(null);
  const [question, setQuestion] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const { data: analyses } = useAnalyses(activeDataset);
  const askMutation = useAskData(activeDataset || '');
  const autoMutation = useAutoAnalyze(activeDataset || '');

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleAsk = () => {
    if (!question.trim() || !activeDataset) return;
    askMutation.mutate({ question });
    setQuestion('');
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <BarChartIcon color="primary" /> Data Analyst
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Upload datasets, ask questions in natural language, get AI-powered insights and charts
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Datasets */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Datasets</Typography>
                <Button size="small" variant="outlined" startIcon={<UploadFileIcon />}
                  onClick={() => fileRef.current?.click()}>Upload</Button>
              </Box>
              <input type="file" ref={fileRef} accept=".csv,.json,.xlsx,.tsv" onChange={handleUpload} style={{ display: 'none' }} />
              {uploadMutation.isPending && <Alert severity="info" sx={{ mb: 1 }}>Uploading...</Alert>}

              {isLoading ? <Skeleton variant="rectangular" height={200} /> : !datasets?.length ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <UploadFileIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                  <Typography color="text.secondary">Upload a CSV, JSON, or Excel file</Typography>
                </Box>
              ) : (
                datasets.map((d) => (
                  <Card key={d.id} variant="outlined" sx={{
                    mb: 1, cursor: 'pointer',
                    bgcolor: activeDataset === d.id ? 'action.selected' : 'transparent',
                    '&:hover': { bgcolor: 'action.hover' },
                  }} onClick={() => setActiveDataset(d.id)}>
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="subtitle2">{d.name}</Typography>
                        <IconButton size="small" color="error" onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(d.id); }}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                        <Chip label={d.file_type} size="small" variant="outlined" />
                        <Chip label={`${d.row_count} rows`} size="small" variant="outlined" />
                        <Chip label={`${d.column_count} cols`} size="small" variant="outlined" />
                        <Chip label={d.status} size="small" color={STATUS_COLORS[d.status] || 'default'} />
                      </Box>
                    </CardContent>
                  </Card>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Analysis */}
        <Grid item xs={12} md={8}>
          {activeDataset ? (
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Analysis</Typography>
                  <Button size="small" variant="outlined" startIcon={
                    autoMutation.isPending ? <CircularProgress size={14} /> : <AutoAwesomeIcon />
                  } onClick={() => autoMutation.mutate('standard')} disabled={autoMutation.isPending}>
                    Auto-Analyze
                  </Button>
                </Box>

                <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
                  <TextField fullWidth size="small" placeholder="Ask a question about your data..."
                    value={question} onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleAsk(); }} />
                  <IconButton color="primary" onClick={handleAsk} disabled={!question.trim() || askMutation.isPending}>
                    {askMutation.isPending ? <CircularProgress size={20} /> : <SendIcon />}
                  </IconButton>
                </Box>

                <Divider sx={{ mb: 2 }} />

                {!analyses?.length ? (
                  <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                    Ask a question or click "Auto-Analyze" to get started
                  </Typography>
                ) : (
                  analyses.map((a) => (
                    <Card key={a.id} variant="outlined" sx={{ mb: 2 }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="subtitle2" color="primary">{a.question}</Typography>
                          <Chip label={a.status} size="small" color={STATUS_COLORS[a.status] || 'default'} />
                        </Box>
                        {a.answer && (
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>{a.answer}</Typography>
                        )}
                        {a.insights.length > 0 && (
                          <Box sx={{ mb: 1 }}>
                            {a.insights.map((ins, i) => (
                              <Alert key={i} severity="info" sx={{ mb: 0.5, py: 0 }}>
                                <Typography variant="caption">[{ins.category}] {ins.insight}</Typography>
                              </Alert>
                            ))}
                          </Box>
                        )}
                        {a.charts.length > 0 && (
                          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                            {a.charts.map((c, i) => (
                              <Chip key={i} label={`${c.type}: ${c.title}`} size="small" variant="outlined" />
                            ))}
                          </Box>
                        )}
                        {a.error && <Alert severity="error" sx={{ mt: 1 }}>{a.error}</Alert>}
                      </CardContent>
                    </Card>
                  ))
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <BarChartIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">Select a dataset to start analyzing</Typography>
                <Typography variant="body2" color="text.secondary">Upload CSV, JSON, or Excel files and ask questions in natural language</Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
