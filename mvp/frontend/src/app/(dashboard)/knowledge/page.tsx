'use client';

import { useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Skeleton,
  TextField,
  Typography,
} from '@mui/material';

import {
  useAsk,
  useDeleteDocument,
  useDocuments,
  useSearch,
  useUploadDocument,
} from '@/features/knowledge/hooks/useKnowledge';

const STATUS_COLORS: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
  pending: 'default',
  processing: 'primary',
  indexed: 'success',
  failed: 'error',
};

export default function KnowledgePage() {
  const { data: documents, isLoading } = useDocuments();
  const uploadMutation = useUploadDocument();
  const deleteMutation = useDeleteDocument();
  const searchMutation = useSearch();
  const askMutation = useAsk();

  const fileRef = useRef<HTMLInputElement>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [question, setQuestion] = useState('');

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
    if (fileRef.current) fileRef.current.value = '';
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Knowledge Base
      </Typography>

      {/* Upload Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Upload Document</Typography>
          <input
            type="file"
            ref={fileRef}
            accept=".txt,.md,.csv"
            onChange={handleUpload}
            style={{ display: 'none' }}
          />
          <Button
            variant="contained"
            onClick={() => fileRef.current?.click()}
            disabled={uploadMutation.isPending}
          >
            {uploadMutation.isPending ? (
              <><CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />Uploading...</>
            ) : 'Upload File'}
          </Button>
          <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
            Supported: TXT, MD, CSV (max 10 MB)
          </Typography>
          {uploadMutation.isError && (
            <Alert severity="error" sx={{ mt: 1 }}>{uploadMutation.error?.message}</Alert>
          )}
          {uploadMutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 1 }}>Document uploaded and indexed.</Alert>
          )}
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Documents List */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Documents</Typography>
              {isLoading ? (
                <Skeleton variant="rectangular" height={200} />
              ) : !documents?.length ? (
                <Typography variant="body2" color="text.secondary">
                  No documents uploaded yet.
                </Typography>
              ) : (
                <List dense>
                  {documents.map((doc) => (
                    <ListItem
                      key={doc.id}
                      secondaryAction={
                        <Button
                          size="small"
                          color="error"
                          onClick={() => deleteMutation.mutate(doc.id)}
                          disabled={deleteMutation.isPending}
                        >
                          Delete
                        </Button>
                      }
                    >
                      <ListItemText
                        primary={doc.filename}
                        secondary={`${doc.total_chunks} chunks`}
                      />
                      <Chip
                        label={doc.status}
                        size="small"
                        color={STATUS_COLORS[doc.status] || 'default'}
                        sx={{ mr: 1 }}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Search + Ask */}
        <Grid item xs={12} md={6}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Search</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Search your documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <Button
                  variant="outlined"
                  onClick={() => searchMutation.mutate(searchQuery)}
                  disabled={!searchQuery.trim() || searchMutation.isPending}
                >
                  Search
                </Button>
              </Box>
              {searchMutation.data && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {searchMutation.data.total} results
                  </Typography>
                  {searchMutation.data.results.map((r, i) => (
                    <Card key={i} variant="outlined" sx={{ mb: 1, p: 1 }}>
                      <Typography variant="caption" color="primary">{r.filename} (score: {r.score})</Typography>
                      <Typography variant="body2" sx={{ mt: 0.5 }}>
                        {r.content.substring(0, 200)}...
                      </Typography>
                    </Card>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Ask a Question (RAG)</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Ask a question about your documents..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                />
                <Button
                  variant="contained"
                  onClick={() => askMutation.mutate(question)}
                  disabled={!question.trim() || askMutation.isPending}
                >
                  {askMutation.isPending ? <CircularProgress size={20} color="inherit" /> : 'Ask'}
                </Button>
              </Box>
              {askMutation.data && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body1" sx={{ mb: 1, whiteSpace: 'pre-wrap' }}>
                    {askMutation.data.answer}
                  </Typography>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="caption" color="text.secondary">
                    Provider: {askMutation.data.provider} | Sources: {askMutation.data.sources.length}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
