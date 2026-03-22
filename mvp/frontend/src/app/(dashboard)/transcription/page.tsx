/**
 * Transcription Page
 * YouTube transcription management with result display, export, and language selection
 */

'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  FormControl,
  IconButton,
  InputLabel,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Stack,
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
import {
  Close,
  ContentCopy,
  Delete,
  Download,
  ExpandMore,
  Refresh,
  Subtitles,
  Visibility,
} from '@mui/icons-material';
import { useCallback, useMemo, useState } from 'react';
import { Controller, useForm } from 'react-hook-form';

import {
  useCreateTranscription,
  useDeleteTranscription,
  useTranscriptions,
} from '@/features/transcription/hooks';
import {
  LANGUAGE_OPTIONS,
  transcriptionCreateSchema,
  type TranscriptionCreateSchema,
} from '@/features/transcription/schemas';
import type { Transcription } from '@/features/transcription/types';
import { TranscriptionStatus } from '@/features/transcription/types';

/* ========================================================================
   CONSTANTS
   ======================================================================== */

const LANGUAGE_LABEL_MAP: Record<string, string> = {
  auto: 'Auto-detect',
  fr: 'French',
  en: 'English',
  ar: 'Arabic',
  es: 'Spanish',
  de: 'German',
};

/* ========================================================================
   HELPER FUNCTIONS
   ======================================================================== */

function getStatusColor(
  status: TranscriptionStatus
): 'default' | 'primary' | 'success' | 'error' {
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

function formatDate(dateString: string | null): string {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleString();
}

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return '-';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function getLanguageLabel(code: string | null): string {
  if (!code) return '-';
  return LANGUAGE_LABEL_MAP[code] ?? code.toUpperCase();
}

/**
 * Generate a basic SRT subtitle file from text and duration.
 * Splits text into segments of roughly 10 words each
 * and distributes timestamps evenly across the duration.
 */
function generateSrt(text: string, durationSeconds: number | null): string {
  const words = text.split(/\s+/).filter(Boolean);
  const segmentSize = 10;
  const segments: string[] = [];

  for (let i = 0; i < words.length; i += segmentSize) {
    segments.push(words.slice(i, i + segmentSize).join(' '));
  }

  const totalDuration = durationSeconds ?? segments.length * 5;
  const segmentDuration = totalDuration / segments.length;

  const formatSrtTime = (totalSecs: number): string => {
    const hours = Math.floor(totalSecs / 3600);
    const mins = Math.floor((totalSecs % 3600) / 60);
    const secs = Math.floor(totalSecs % 60);
    const ms = Math.round((totalSecs % 1) * 1000);
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
  };

  return segments
    .map((segment, index) => {
      const start = index * segmentDuration;
      const end = (index + 1) * segmentDuration;
      return `${index + 1}\n${formatSrtTime(start)} --> ${formatSrtTime(end)}\n${segment}`;
    })
    .join('\n\n');
}

function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function extractVideoId(url: string): string {
  const match = url.match(/(?:v=|youtu\.be\/)([\w-]{11})/);
  return match?.[1] ?? 'transcription';
}

/* ========================================================================
   SUB-COMPONENTS
   ======================================================================== */

interface ExportButtonsProps {
  transcription: Transcription;
}

function ExportButtons({ transcription }: ExportButtonsProps): JSX.Element | null {
  const [copied, setCopied] = useState(false);

  if (transcription.status !== TranscriptionStatus.COMPLETED || !transcription.text) {
    return null;
  }

  const videoId = extractVideoId(transcription.video_url);

  const handleCopy = async (): Promise<void> => {
    await navigator.clipboard.writeText(transcription.text ?? '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadTxt = (): void => {
    downloadFile(
      transcription.text ?? '',
      `transcription-${videoId}.txt`,
      'text/plain'
    );
  };

  const handleDownloadSrt = (): void => {
    const srt = generateSrt(transcription.text ?? '', transcription.duration_seconds);
    downloadFile(srt, `transcription-${videoId}.srt`, 'text/srt');
  };

  return (
    <Stack direction="row" spacing={1}>
      <Tooltip title={copied ? 'Copied!' : 'Copy to clipboard'}>
        <Button
          size="small"
          variant="outlined"
          startIcon={<ContentCopy />}
          onClick={() => void handleCopy()}
        >
          {copied ? 'Copied' : 'Copy'}
        </Button>
      </Tooltip>
      <Tooltip title="Download as plain text file">
        <Button
          size="small"
          variant="outlined"
          startIcon={<Download />}
          onClick={handleDownloadTxt}
        >
          TXT
        </Button>
      </Tooltip>
      <Tooltip title="Download as SRT subtitle file">
        <Button
          size="small"
          variant="outlined"
          startIcon={<Subtitles />}
          onClick={handleDownloadSrt}
        >
          SRT
        </Button>
      </Tooltip>
    </Stack>
  );
}

interface TranscriptionDetailProps {
  transcription: Transcription;
  onClose: () => void;
}

function TranscriptionDetail({ transcription, onClose }: TranscriptionDetailProps): JSX.Element {
  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Transcription Details
          </Typography>
          <IconButton onClick={onClose} size="small" aria-label="Close details">
            <Close />
          </IconButton>
        </Box>

        {/* Metadata row */}
        <Stack direction="row" spacing={3} sx={{ mb: 2, flexWrap: 'wrap' }} useFlexGap>
          <Box>
            <Typography variant="caption" color="text.secondary">Status</Typography>
            <Box>
              <Chip
                label={transcription.status}
                color={getStatusColor(transcription.status)}
                size="small"
              />
            </Box>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">Language</Typography>
            <Typography variant="body2">{getLanguageLabel(transcription.language)}</Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">Duration</Typography>
            <Typography variant="body2">{formatDuration(transcription.duration_seconds)}</Typography>
          </Box>
          {transcription.confidence !== null && (
            <Box sx={{ minWidth: 160 }}>
              <Typography variant="caption" color="text.secondary">
                Confidence: {(transcription.confidence * 100).toFixed(1)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={transcription.confidence * 100}
                color={
                  transcription.confidence >= 0.9
                    ? 'success'
                    : transcription.confidence >= 0.7
                      ? 'primary'
                      : 'warning'
                }
                sx={{ mt: 0.5, height: 6, borderRadius: 3 }}
              />
            </Box>
          )}
          <Box>
            <Typography variant="caption" color="text.secondary">Created</Typography>
            <Typography variant="body2">{formatDate(transcription.created_at)}</Typography>
          </Box>
          {transcription.completed_at && (
            <Box>
              <Typography variant="caption" color="text.secondary">Completed</Typography>
              <Typography variant="body2">{formatDate(transcription.completed_at)}</Typography>
            </Box>
          )}
        </Stack>

        <Divider sx={{ mb: 2 }} />

        {/* Error display */}
        {transcription.error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {transcription.error}
          </Alert>
        )}

        {/* Processing indicator */}
        {transcription.status === TranscriptionStatus.PROCESSING && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Transcription in progress...
            </Typography>
            <LinearProgress />
          </Box>
        )}

        {/* Transcription text */}
        {transcription.text && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                Transcription Text
              </Typography>
              <ExportButtons transcription={transcription} />
            </Box>
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                maxHeight: 400,
                overflow: 'auto',
                bgcolor: 'action.hover',
                fontFamily: 'inherit',
              }}
            >
              <Typography
                variant="body2"
                sx={{
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  lineHeight: 1.7,
                }}
              >
                {transcription.text}
              </Typography>
            </Paper>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              {transcription.text.split(/\s+/).length} words
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

/* ========================================================================
   PAGE COMPONENT
   ======================================================================== */

export default function TranscriptionPage(): JSX.Element {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [deleteDialogId, setDeleteDialogId] = useState<string | null>(null);

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
      language: 'auto',
    },
  });

  /* Handlers */
  const onSubmit = async (formData: TranscriptionCreateSchema): Promise<void> => {
    await createMutation.mutateAsync({
      video_url: formData.video_url,
      language: formData.language === 'auto' ? undefined : formData.language,
    });
    reset();
  };

  const handleDeleteConfirm = async (): Promise<void> => {
    if (deleteDialogId) {
      await deleteMutation.mutateAsync(deleteDialogId);
      if (selectedId === deleteDialogId) {
        setSelectedId(null);
      }
      setDeleteDialogId(null);
    }
  };

  const handleRefresh = useCallback((): void => {
    void refetch();
  }, [refetch]);

  /* Derived state */
  const selectedTranscription = useMemo(() => {
    if (!selectedId || !data?.items) return null;
    return data.items.find(t => t.id === selectedId) ?? null;
  }, [selectedId, data]);

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
        <Tooltip title="Refresh list">
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
              <Controller
                name="language"
                control={control}
                render={({ field }) => (
                  <FormControl sx={{ minWidth: 160 }}>
                    <InputLabel id="language-select-label">Language</InputLabel>
                    <Select
                      {...field}
                      labelId="language-select-label"
                      label="Language"
                      value={field.value ?? 'auto'}
                      aria-label="Select transcription language"
                    >
                      {LANGUAGE_OPTIONS.map(opt => (
                        <MenuItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={isSubmitting || createMutation.isPending}
                sx={{ minWidth: 130, height: 56 }}
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
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <LinearProgress sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Loading transcriptions...
              </Typography>
            </Box>
          ) : !data || data.items.length === 0 ? (
            <Box sx={{ py: 6, textAlign: 'center' }}>
              <Subtitles sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No transcriptions yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Paste a YouTube URL above and click Transcribe to get started.
              </Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table aria-label="Transcriptions table">
                <TableHead>
                  <TableRow>
                    <TableCell>Video URL</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Language</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.items.map(transcription => (
                    <TableRow
                      key={transcription.id}
                      hover
                      selected={selectedId === transcription.id}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell
                        onClick={() =>
                          setSelectedId(prev =>
                            prev === transcription.id ? null : transcription.id
                          )
                        }
                      >
                        <Typography
                          variant="body2"
                          sx={{
                            maxWidth: 320,
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
                          variant={
                            transcription.status === TranscriptionStatus.PROCESSING
                              ? 'outlined'
                              : 'filled'
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {getLanguageLabel(transcription.language)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatDate(transcription.created_at)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                          <Tooltip title="View details">
                            <IconButton
                              size="small"
                              onClick={() =>
                                setSelectedId(prev =>
                                  prev === transcription.id ? null : transcription.id
                                )
                              }
                              color={selectedId === transcription.id ? 'primary' : 'default'}
                              aria-label={`View transcription details`}
                            >
                              {selectedId === transcription.id ? (
                                <ExpandMore />
                              ) : (
                                <Visibility fontSize="small" />
                              )}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              onClick={() => setDeleteDialogId(transcription.id)}
                              disabled={deleteMutation.isPending}
                              aria-label={`Delete transcription`}
                              color="error"
                            >
                              <Delete fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Selected Transcription Detail Panel */}
      <Collapse in={!!selectedTranscription} unmountOnExit>
        {selectedTranscription && (
          <TranscriptionDetail
            transcription={selectedTranscription}
            onClose={() => setSelectedId(null)}
          />
        )}
      </Collapse>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!deleteDialogId}
        onClose={() => setDeleteDialogId(null)}
        aria-labelledby="delete-dialog-title"
      >
        <DialogTitle id="delete-dialog-title">Delete Transcription</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this transcription? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogId(null)} color="inherit">
            Cancel
          </Button>
          <Button
            onClick={() => void handleDeleteConfirm()}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
