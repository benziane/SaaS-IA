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
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  Grid,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Skeleton,
  TextField,
  Typography,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

import {
  useAsk,
  useDeleteDocument,
  useDocumentChunks,
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
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [selectedDocName, setSelectedDocName] = useState<string>('');

  const { data: chunks, isLoading: chunksLoading } = useDocumentChunks(selectedDocId);

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleViewChunks = (id: string, name: string) => {
    setSelectedDocId(id);
    setSelectedDocName(name);
  };

  const handleCloseModal = () => {
    setSelectedDocId(null);
    setSelectedDocName('');
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
                      disablePadding
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
                      <ListItemButton
                        onClick={() => handleViewChunks(doc.id, doc.filename)}
                        disabled={doc.status !== 'indexed'}
                        sx={{ pr: 10 }}
                      >
                        <ListItemText
                          primary={doc.filename}
                          secondary={`${doc.total_chunks} chunks — cliquer pour voir`}
                        />
                        <Chip
                          label={doc.status}
                          size="small"
                          color={STATUS_COLORS[doc.status] || 'default'}
                          sx={{ mr: 1 }}
                        />
                      </ListItemButton>
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

      {/* Document Chunks Viewer Modal */}
      <Dialog open={!!selectedDocId} onClose={handleCloseModal} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h6">{selectedDocName}</Typography>
            {chunks && (
              <Typography variant="caption" color="text.secondary">
                {chunks.length} chunk(s)
              </Typography>
            )}
          </Box>
          <IconButton onClick={handleCloseModal} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers sx={{ maxHeight: '70vh', overflowY: 'auto' }}>
          {chunksLoading ? (
            <CircularProgress />
          ) : !chunks?.length ? (
            <Typography color="text.secondary">Aucun chunk disponible.</Typography>
          ) : (
            chunks.map((chunk) => (
              <Box key={chunk.id} sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  Chunk #{chunk.chunk_index + 1}
                </Typography>
                <Box
                  sx={{
                    p: 1.5,
                    bgcolor: 'action.hover',
                    borderRadius: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.8rem',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {chunk.content}
                </Box>
                {chunk.chunk_index < chunks.length - 1 && <Divider sx={{ mt: 2 }} />}
              </Box>
            ))
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}
