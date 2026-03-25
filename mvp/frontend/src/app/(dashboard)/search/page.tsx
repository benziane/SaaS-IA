'use client';

import { useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  Divider, Grid, IconButton, TextField, Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import apiClient from '@/lib/apiClient';

interface SearchResultItem {
  id: string; type: string; title: string; content: string;
  score: number; url: string; _module: string;
  [key: string]: unknown;
}

const MODULE_ICONS: Record<string, string> = {
  transcriptions: '🎤', knowledge: '📚', content: '✨', conversations: '💬',
};
const MODULE_COLORS: Record<string, string> = {
  transcriptions: '#e3f2fd', knowledge: '#e8f5e9', content: '#fce4ec', conversations: '#f3e5f5',
};

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [facets, setFacets] = useState<Record<string, number>>({});
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [answerLoading, setAnswerLoading] = useState(false);
  const [total, setTotal] = useState(0);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true); setAnswer('');
    try {
      const resp = await apiClient.get('/api/search/', { params: { q: query } });
      setResults(resp.data.results || []);
      setFacets(resp.data.facets || {});
      setTotal(resp.data.total || 0);
    } catch { setResults([]); }
    setLoading(false);
  };

  const handleAskAnswer = async () => {
    if (!query.trim()) return;
    setAnswerLoading(true);
    try {
      const resp = await apiClient.get('/api/search/answer', { params: { q: query } });
      setAnswer(resp.data.answer || '');
      if (!results.length && resp.data.sources) {
        setResults(resp.data.sources);
        setFacets(resp.data.facets || {});
      }
    } catch { setAnswer('Failed to generate answer.'); }
    setAnswerLoading(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SearchIcon color="primary" /> Universal Search
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Search across all platform data: transcriptions, documents, content, conversations
        </Typography>
      </Box>

      {/* Search Bar */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField fullWidth placeholder="Search across all your platform data..."
              value={query} onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(); }} />
            <Button variant="contained" startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <SearchIcon />}
              onClick={handleSearch} disabled={!query.trim() || loading}>
              Search
            </Button>
            <Button variant="outlined" startIcon={answerLoading ? <CircularProgress size={18} /> : <AutoAwesomeIcon />}
              onClick={handleAskAnswer} disabled={!query.trim() || answerLoading}>
              Ask AI
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* AI Answer */}
      {answer && (
        <Card sx={{ mb: 3, bgcolor: 'action.hover' }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <AutoAwesomeIcon fontSize="small" color="primary" /> AI Answer
            </Typography>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>{answer}</Typography>
          </CardContent>
        </Card>
      )}

      {/* Facets + Results */}
      {total > 0 && (
        <Grid container spacing={3}>
          {/* Facets */}
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Sources ({total} results)</Typography>
                {Object.entries(facets).map(([module, count]) => (
                  <Box key={module} sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Chip label={`${MODULE_ICONS[module] || '📄'} ${module}`} size="small"
                      sx={{ bgcolor: MODULE_COLORS[module] || '#f5f5f5' }} />
                    <Typography variant="body2" fontWeight="bold">{count}</Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>

          {/* Results */}
          <Grid item xs={12} md={9}>
            {results.map((r, i) => (
              <Card key={i} variant="outlined" sx={{ mb: 1 }}>
                <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Chip label={`${MODULE_ICONS[r._module] || '📄'} ${r._module}`} size="small"
                      sx={{ bgcolor: MODULE_COLORS[r._module] || '#f5f5f5' }} />
                    <Typography variant="subtitle2">{r.title}</Typography>
                    <Chip label={`${(r.score * 100).toFixed(0)}%`} size="small" variant="outlined" sx={{ ml: 'auto' }} />
                  </Box>
                  <Typography variant="body2" color="text.secondary"
                    sx={{ overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                    {r.content}
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Grid>
        </Grid>
      )}

      {!loading && total === 0 && query && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <SearchIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography color="text.secondary">No results found. Try a different query.</Typography>
        </Box>
      )}
    </Box>
  );
}
