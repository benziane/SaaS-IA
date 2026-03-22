'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Skeleton,
  TextField,
  Typography,
} from '@mui/material';

import { useAPIKeys, useCreateAPIKey, useRevokeAPIKey } from '@/features/api-keys/hooks/useAPIKeys';
import type { APIKeyCreated } from '@/features/api-keys/types';

const API_EXAMPLES = [
  {
    title: 'Transcribe a video',
    method: 'POST',
    endpoint: '/v1/transcribe',
    curl: `curl -X POST http://localhost:8004/v1/transcribe \\
  -H "X-API-Key: YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"video_url": "https://youtube.com/watch?v=...", "language": "auto"}'`,
  },
  {
    title: 'Process text with AI',
    method: 'POST',
    endpoint: '/v1/process',
    curl: `curl -X POST http://localhost:8004/v1/process \\
  -H "X-API-Key: YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Your text here", "task": "summarize", "provider": "gemini"}'`,
  },
  {
    title: 'Check job status',
    method: 'GET',
    endpoint: '/v1/jobs/{job_id}',
    curl: `curl http://localhost:8004/v1/jobs/JOB_ID \\
  -H "X-API-Key: YOUR_KEY"`,
  },
];

export default function APIDocsPage() {
  const { data: keys, isLoading } = useAPIKeys();
  const createMutation = useCreateAPIKey();
  const revokeMutation = useRevokeAPIKey();
  const [createOpen, setCreateOpen] = useState(false);
  const [keyName, setKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState<APIKeyCreated | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCreate = () => {
    if (!keyName.trim()) return;
    createMutation.mutate(
      { name: keyName.trim() },
      {
        onSuccess: (data) => {
          setCreatedKey(data);
          setCreateOpen(false);
          setKeyName('');
        },
      }
    );
  };

  const handleCopy = () => {
    if (createdKey) {
      navigator.clipboard.writeText(createdKey.key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        API Documentation & Keys
      </Typography>

      {/* Created Key Alert */}
      {createdKey && (
        <Alert severity="warning" sx={{ mb: 3 }} onClose={() => setCreatedKey(null)}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Your API key (save it now - it won't be shown again):
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <code style={{ fontSize: '0.9rem', wordBreak: 'break-all' }}>{createdKey.key}</code>
            <Button size="small" onClick={handleCopy}>
              {copied ? 'Copied!' : 'Copy'}
            </Button>
          </Box>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* API Keys Management */}
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">API Keys</Typography>
                <Button variant="contained" size="small" onClick={() => setCreateOpen(true)}>
                  Create Key
                </Button>
              </Box>

              {isLoading ? (
                <Skeleton variant="rectangular" height={150} />
              ) : !keys?.length ? (
                <Typography variant="body2" color="text.secondary">
                  No API keys created yet.
                </Typography>
              ) : (
                <List dense>
                  {keys.map((key) => (
                    <ListItem
                      key={key.id}
                      secondaryAction={
                        key.is_active ? (
                          <Button
                            size="small"
                            color="error"
                            onClick={() => revokeMutation.mutate(key.id)}
                          >
                            Revoke
                          </Button>
                        ) : (
                          <Chip label="Revoked" size="small" color="default" />
                        )
                      }
                    >
                      <ListItemText
                        primary={key.name}
                        secondary={
                          <>
                            {key.key_prefix}... |{' '}
                            {key.last_used_at
                              ? `Last used: ${new Date(key.last_used_at).toLocaleDateString()}`
                              : 'Never used'}
                          </>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* API Documentation */}
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Public API v1
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Authenticate using the <code>X-API-Key</code> header with your API key.
              </Typography>

              {API_EXAMPLES.map((example, idx) => (
                <Box key={idx} sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Chip label={example.method} size="small" color="primary" />
                    <Typography variant="subtitle2">{example.endpoint}</Typography>
                  </Box>
                  <Typography variant="body2" sx={{ mb: 1 }}>{example.title}</Typography>
                  <Box
                    sx={{
                      bgcolor: 'grey.900',
                      color: 'grey.100',
                      p: 2,
                      borderRadius: 1,
                      fontFamily: 'monospace',
                      fontSize: '0.8rem',
                      whiteSpace: 'pre-wrap',
                      overflow: 'auto',
                    }}
                  >
                    {example.curl}
                  </Box>
                  {idx < API_EXAMPLES.length - 1 && <Divider sx={{ mt: 2 }} />}
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Create Key Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create API Key</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Key Name"
            value={keyName}
            onChange={(e) => setKeyName(e.target.value)}
            placeholder="e.g., Production, Testing"
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!keyName.trim() || createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
