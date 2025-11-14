/**
 * Transcription Page - Grade S++
 * YouTube transcription management page
 */

'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { Delete, Refresh } from '@mui/icons-material';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';

import {
  useCreateTranscription,
  useDeleteTranscription,
  useTranscriptions,
} from '@/features/transcription/hooks';
import {
  transcriptionCreateSchema,
  type TranscriptionCreateSchema,
} from '@/features/transcription/schemas';
import { TranscriptionStatus } from '@/features/transcription/types';

/* ========================================================================
   HELPER FUNCTIONS
   ======================================================================== */

function getStatusColor(
  status: TranscriptionStatus
): 'default' | 'primary' | 'success' | 'error' | 'warning' {
  switch (status) {
    case TranscriptionStatus.PENDING:
      return 'default';
    case TranscriptionStatus.PROCESSING:
      return 'primary';
    case TranscriptionStatus.COMPLETED:
      return 'success';
    case TranscriptionStatus.FAILED:
      return 'error';
    default:
      return 'default';
  }
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString();
}

/* ========================================================================
   PAGE COMPONENT
   ======================================================================== */

export default function TranscriptionPage(): JSX.Element {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  
  /* Queries & Mutations */
  const { data, isLoading, refetch } = useTranscriptions();
  const createMutation = useCreateTranscription();
  const deleteMutation = useDeleteTranscription();
  
  /* Form */
  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<TranscriptionCreateSchema>({
    resolver: zodResolver(transcriptionCreateSchema),
    defaultValues: {
      video_url: '',
    },
  });
  
  /* Handlers */
  const onSubmit = async (formData: TranscriptionCreateSchema): Promise<void> => {
    await createMutation.mutateAsync(formData);
    reset();
  };
  
  const handleDelete = async (id: string): Promise<void> => {
    if (window.confirm('Are you sure you want to delete this transcription?')) {
      await deleteMutation.mutateAsync(id);
    }
  };
  
  const handleRefresh = (): void => {
    void refetch();
  };
  
  /* ========================================================================
     RENDER
     ======================================================================== */
  
  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
            YouTube Transcriptions
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Transcribe YouTube videos using AI
          </Typography>
        </Box>
        <Tooltip title="Refresh">
          <IconButton onClick={handleRefresh} aria-label="Refresh transcriptions">
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>
      
      {/* Create Form */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
            New Transcription
          </Typography>
          <form onSubmit={handleSubmit(onSubmit)}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
              <Controller
                name="video_url"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="YouTube Video URL"
                    placeholder="https://www.youtube.com/watch?v=..."
                    error={!!errors.video_url}
                    helperText={errors.video_url?.message}
                    inputProps={{
                      'aria-label': 'YouTube video URL',
                      'aria-required': 'true',
                      'aria-invalid': !!errors.video_url,
                    }}
                  />
                )}
              />
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={isSubmitting || createMutation.isPending}
                sx={{ minWidth: 120 }}
                aria-label="Start transcription"
              >
                {isSubmitting || createMutation.isPending ? 'Starting...' : 'Transcribe'}
              </Button>
            </Box>
          </form>
        </CardContent>
      </Card>
      
      {/* Transcriptions Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
            Your Transcriptions
          </Typography>
          
          {isLoading ? (
            <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
              Loading transcriptions...
            </Typography>
          ) : !data || data.items.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
              No transcriptions yet. Create your first one above!
            </Typography>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table aria-label="Transcriptions table">
                <TableHead>
                  <TableRow>
                    <TableCell>Video URL</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.items.map(transcription => (
                    <TableRow
                      key={transcription.id}
                      hover
                      selected={selectedId === transcription.id}
                      onClick={() => setSelectedId(transcription.id)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{
                            maxWidth: 300,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {transcription.video_url}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={transcription.status}
                          color={getStatusColor(transcription.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatDate(transcription.created_at)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {transcription.confidence !== null ? (
                          <Typography variant="body2">
                            {(transcription.confidence * 100).toFixed(1)}%
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            onClick={e => {
                              e.stopPropagation();
                              void handleDelete(transcription.id);
                            }}
                            disabled={deleteMutation.isPending}
                            aria-label={`Delete transcription ${transcription.id}`}
                          >
                            <Delete fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
      
      {/* Selected Transcription Details */}
      {selectedId && data?.items.find(t => t.id === selectedId) && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Transcription Details
            </Typography>
            {(() => {
              const selected = data.items.find(t => t.id === selectedId);
              if (!selected) {
                return null;
              }
              
              return (
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    <strong>ID:</strong> {selected.id}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    <strong>Status:</strong> {selected.status}
                  </Typography>
                  {selected.error && (
                    <Typography variant="body2" color="error" sx={{ mb: 1 }}>
                      <strong>Error:</strong> {selected.error}
                    </Typography>
                  )}
                  {selected.text && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                        Transcription:
                      </Typography>
                      <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                          {selected.text}
                        </Typography>
                      </Paper>
                    </Box>
                  )}
                </Box>
              );
            })()}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

