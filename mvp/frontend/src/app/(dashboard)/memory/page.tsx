'use client';

import { useEffect, useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  Dialog, DialogActions, DialogContent, DialogTitle, Divider,
  FormControl, Grid, IconButton, InputLabel, MenuItem, Select,
  TextField, Typography,
} from '@mui/material';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import DeleteForeverIcon from '@mui/icons-material/DeleteForever';
import apiClient from '@/lib/apiClient';

interface Memory {
  id: string; memory_type: string; content: string; category: string | null;
  confidence: number; source: string; active: boolean; use_count: number;
  created_at: string;
}

const TYPE_ICONS: Record<string, string> = {
  preference: '⭐', fact: '📌', context: '🎯', instruction: '📋',
};
const TYPE_COLORS: Record<string, 'primary' | 'success' | 'info' | 'warning'> = {
  preference: 'primary', fact: 'success', context: 'info', instruction: 'warning',
};

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [context, setContext] = useState('');
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [extractOpen, setExtractOpen] = useState(false);
  const [newContent, setNewContent] = useState('');
  const [newType, setNewType] = useState('fact');
  const [extractText, setExtractText] = useState('');
  const [extracting, setExtracting] = useState(false);

  const fetchData = async () => {
    try {
      const [memResp, ctxResp] = await Promise.all([
        apiClient.get('/api/memory/'),
        apiClient.get('/api/memory/context'),
      ]);
      setMemories(memResp.data || []);
      setContext(ctxResp.data?.context || '');
    } catch {}
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleAdd = async () => {
    if (!newContent.trim()) return;
    await apiClient.post('/api/memory/', { content: newContent, memory_type: newType });
    setAddOpen(false); setNewContent('');
    fetchData();
  };

  const handleDelete = async (id: string) => {
    await apiClient.delete(`/api/memory/${id}`);
    fetchData();
  };

  const handleExtract = async () => {
    if (!extractText.trim()) return;
    setExtracting(true);
    try {
      const resp = await apiClient.post('/api/memory/extract', { text: extractText, source: 'manual' });
      setExtractOpen(false); setExtractText('');
      fetchData();
    } catch {}
    setExtracting(false);
  };

  const handleForgetAll = async () => {
    if (!confirm('Are you sure? This will deactivate ALL memories (RGPD).')) return;
    await apiClient.delete('/api/memory/forget-all');
    fetchData();
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PsychologyIcon color="primary" /> AI Memory
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Your AI remembers preferences, facts, and context to personalize all responses
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<AutoAwesomeIcon />} onClick={() => setExtractOpen(true)}>
            Auto-Extract
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setAddOpen(true)}>
            Add Memory
          </Button>
        </Box>
      </Box>

      {/* Context Preview */}
      {context && (
        <Card sx={{ mb: 3, bgcolor: 'action.hover' }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Context Injected into AI Prompts</Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.85rem' }}>
              {context}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Memories */}
      <Grid container spacing={2}>
        {loading ? (
          <Grid item xs={12}><CircularProgress /></Grid>
        ) : memories.length === 0 ? (
          <Grid item xs={12}>
            <Card><CardContent sx={{ textAlign: 'center', py: 6 }}>
              <PsychologyIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
              <Typography color="text.secondary">No memories yet. Add one or auto-extract from text.</Typography>
            </CardContent></Card>
          </Grid>
        ) : (
          memories.map((mem) => (
            <Grid item xs={12} sm={6} md={4} key={mem.id}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Chip label={`${TYPE_ICONS[mem.memory_type] || '📌'} ${mem.memory_type}`}
                      size="small" color={TYPE_COLORS[mem.memory_type] || 'default'} />
                    <IconButton size="small" color="error" onClick={() => handleDelete(mem.id)}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                  <Typography variant="body2" sx={{ mb: 1 }}>{mem.content}</Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {mem.category && <Chip label={mem.category} size="small" variant="outlined" />}
                    <Chip label={`${(mem.confidence * 100).toFixed(0)}%`} size="small" variant="outlined" />
                    <Chip label={`used ${mem.use_count}x`} size="small" variant="outlined" />
                    <Chip label={mem.source} size="small" variant="outlined" />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))
        )}
      </Grid>

      {memories.length > 0 && (
        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Button color="error" startIcon={<DeleteForeverIcon />} onClick={handleForgetAll}>
            Forget All (RGPD)
          </Button>
        </Box>
      )}

      {/* Add Memory Dialog */}
      <Dialog open={addOpen} onClose={() => setAddOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Memory</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Memory content" placeholder="e.g., I prefer formal tone..."
            value={newContent} onChange={(e) => setNewContent(e.target.value)} sx={{ mt: 1, mb: 2 }} multiline rows={2} />
          <FormControl fullWidth size="small">
            <InputLabel>Type</InputLabel>
            <Select value={newType} label="Type" onChange={(e) => setNewType(e.target.value)}>
              <MenuItem value="preference">Preference</MenuItem>
              <MenuItem value="fact">Fact</MenuItem>
              <MenuItem value="context">Context</MenuItem>
              <MenuItem value="instruction">Instruction</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleAdd} disabled={!newContent.trim()}>Add</Button>
        </DialogActions>
      </Dialog>

      {/* Extract Dialog */}
      <Dialog open={extractOpen} onClose={() => setExtractOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Auto-Extract Memories from Text</DialogTitle>
        <DialogContent>
          <TextField fullWidth multiline rows={6} label="Paste any text"
            placeholder="Paste a conversation, notes, or any text. AI will extract preferences, facts, and instructions..."
            value={extractText} onChange={(e) => setExtractText(e.target.value)} sx={{ mt: 1 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExtractOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleExtract} disabled={!extractText.trim() || extracting}
            startIcon={extracting ? <CircularProgress size={16} color="inherit" /> : <AutoAwesomeIcon />}>
            Extract
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
