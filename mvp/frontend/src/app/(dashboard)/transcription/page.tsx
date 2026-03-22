/**
 * Transcription Page
 * Multi-source transcription management with YouTube/URL input, file upload,
 * result display, export, and language selection.
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
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  AudioFile,
  AutoFixHigh,
  Chat,
  Close,
  CloudUpload,
  ContentCopy,
  Delete,
  Download,
  ExpandMore,
  InsertLink,
  Mic,
  Refresh,
  Stop,
  Subtitles,
  Visibility,
} from '@mui/icons-material';
import { useCallback, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Controller, useForm } from 'react-hook-form';

import {
  useCreateTranscription,
  useDeleteTranscription,
  useTranscriptions,
  useUploadTranscription,
} from '@/features/transcription/hooks';
import { useSSE } from '@/hooks/useSSE';
import { StreamingText } from '@/components/ui/StreamingText';
import AudioRecorder from '@/components/ui/AudioRecorder';
import {
  LANGUAGE_OPTIONS,
  transcriptionCreateSchema,
  type TranscriptionCreateSchema,
} from '@/features/transcription/schemas';
import type { Transcription, TranscriptionSourceType } from '@/features/transcription/types';
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

const ACCEPTED_FILE_TYPES = [
  'audio/mpeg',
  'audio/wav',
  'audio/mp4',
  'audio/x-m4a',
  'audio/ogg',
  'audio/webm',
  'audio/flac',
  'video/mp4',
  'video/webm',
];

const ACCEPTED_EXTENSIONS = '.mp3,.wav,.mp4,.m4a,.ogg,.webm,.flac';

const MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024; // 500 MB

const ACCEPTED_FORMATS_DISPLAY = 'MP3, WAV, MP4, M4A, OGG, WEBM, FLAC';

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

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getSourceIcon(sourceType: TranscriptionSourceType | undefined): JSX.Element {
  switch (sourceType) {
    case 'upload':
      return <AudioFile fontSize="small" sx={{ color: 'info.main' }} />;
    case 'url':
      return <InsertLink fontSize="small" sx={{ color: 'warning.main' }} />;
    case 'youtube':
    default:
      return <Subtitles fontSize="small" sx={{ color: 'error.main' }} />;
  }
}

function getSourceLabel(sourceType: TranscriptionSourceType | undefined): string {
  switch (sourceType) {
    case 'upload':
      return 'Upload';
    case 'url':
      return 'URL';
    case 'youtube':
    default:
      return 'YouTube';
  }
}

function getSourceDisplay(transcription: Transcription): string {
  if (transcription.source_type === 'upload' && transcription.original_filename) {
    return transcription.original_filename;
  }
  return transcription.video_url;
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
  const router = useRouter();
  const { startStream, stopStream, isStreaming } = useSSE();
  const [improvedText, setImprovedText] = useState('');
  const [streamDone, setStreamDone] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [streamProvider, setStreamProvider] = useState<string | undefined>(undefined);
  const [streamTokenCount, setStreamTokenCount] = useState<number | undefined>(undefined);
  const [copiedImproved, setCopiedImproved] = useState(false);
  const accumulatedTextRef = useRef('');

  const handleImproveWithAI = (): void => {
    // Reset state for a new stream
    setImprovedText('');
    setStreamDone(false);
    setStreamError(null);
    setStreamProvider(undefined);
    setStreamTokenCount(undefined);
    accumulatedTextRef.current = '';

    startStream(
      '/api/ai-assistant/stream',
      { text: transcription.text ?? '' },
      {
        onToken: (token: string) => {
          accumulatedTextRef.current += token;
          setImprovedText(accumulatedTextRef.current);
        },
        onDone: (info) => {
          setStreamDone(true);
          setStreamProvider(info.provider);
          setStreamTokenCount(info.tokens_streamed);
        },
        onError: (error: string) => {
          setStreamError(error);
        },
      }
    );
  };

  const handleCopyImproved = async (): Promise<void> => {
    await navigator.clipboard.writeText(improvedText);
    setCopiedImproved(true);
    setTimeout(() => setCopiedImproved(false), 2000);
  };

  const showImprovedSection = isStreaming || streamDone || !!streamError;
  const showOriginalText = !streamDone;

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
                {streamDone ? 'Original Transcription' : 'Transcription Text'}
              </Typography>
              <Stack direction="row" spacing={1} alignItems="center">
                <ExportButtons transcription={transcription} />
                {transcription.status === TranscriptionStatus.COMPLETED && !isStreaming && (
                  <>
                    <Tooltip title="Chat with AI about this transcription">
                      <Button
                        size="small"
                        variant="outlined"
                        color="primary"
                        startIcon={<Chat />}
                        onClick={() => router.push(`/chat?transcription_id=${transcription.id}`)}
                      >
                        Chat about this
                      </Button>
                    </Tooltip>
                    <Tooltip title="Improve transcription text using AI">
                      <Button
                        size="small"
                        variant="outlined"
                        color="secondary"
                        startIcon={<AutoFixHigh />}
                        onClick={handleImproveWithAI}
                      >
                        Improve with AI
                      </Button>
                    </Tooltip>
                  </>
                )}
                {isStreaming && (
                  <Tooltip title="Stop AI streaming">
                    <Button
                      size="small"
                      variant="outlined"
                      color="warning"
                      startIcon={<Stop />}
                      onClick={stopStream}
                    >
                      Stop
                    </Button>
                  </Tooltip>
                )}
              </Stack>
            </Box>

            {showOriginalText && (
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
            )}
            {showOriginalText && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {transcription.text.split(/\s+/).length} words
              </Typography>
            )}

            {/* AI-Improved Text Section */}
            {showImprovedSection && (
              <Box sx={{ mt: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    AI-Improved Text
                  </Typography>
                  {streamDone && (
                    <Tooltip title={copiedImproved ? 'Copied!' : 'Copy improved text to clipboard'}>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<ContentCopy />}
                        onClick={() => void handleCopyImproved()}
                      >
                        {copiedImproved ? 'Copied' : 'Copy improved text'}
                      </Button>
                    </Tooltip>
                  )}
                </Box>

                {streamError && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {streamError}
                  </Alert>
                )}

                <StreamingText
                  text={improvedText}
                  isStreaming={isStreaming}
                  provider={streamProvider}
                  tokenCount={streamTokenCount}
                />
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

/* ========================================================================
   FILE UPLOAD TAB COMPONENT
   ======================================================================== */

interface FileUploadFormProps {
  onUploadComplete: () => void;
}

function FileUploadForm({ onUploadComplete }: FileUploadFormProps): JSX.Element {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLanguage, setUploadLanguage] = useState<string>('auto');
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [dragOver, setDragOver] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useUploadTranscription((progress) => {
    setUploadProgress(progress);
  });

  const validateFile = (file: File): string | null => {
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File size exceeds the 500 MB limit. Selected file: ${formatFileSize(file.size)}`;
    }
    const isAcceptedType = ACCEPTED_FILE_TYPES.some((type) => file.type === type);
    const hasAcceptedExtension = ACCEPTED_EXTENSIONS.split(',').some((ext) =>
      file.name.toLowerCase().endsWith(ext)
    );
    if (!isAcceptedType && !hasAcceptedExtension) {
      return `Unsupported file format. Accepted formats: ${ACCEPTED_FORMATS_DISPLAY}`;
    }
    return null;
  };

  const handleFileSelect = (file: File): void => {
    const error = validateFile(file);
    if (error) {
      setFileError(error);
      setSelectedFile(null);
      return;
    }
    setFileError(null);
    setSelectedFile(file);
    setUploadProgress(0);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>): void => {
    event.preventDefault();
    setDragOver(false);
    const file = event.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>): void => {
    event.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (): void => {
    setDragOver(false);
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleUploadSubmit = async (): Promise<void> => {
    if (!selectedFile) return;
    setUploadProgress(0);
    await uploadMutation.mutateAsync({
      file: selectedFile,
      language: uploadLanguage === 'auto' ? undefined : uploadLanguage,
    });
    setSelectedFile(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onUploadComplete();
  };

  const handleClearFile = (): void => {
    setSelectedFile(null);
    setFileError(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <Box>
      {/* Drop zone */}
      <Box
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        sx={{
          border: '2px dashed',
          borderColor: dragOver ? 'primary.main' : fileError ? 'error.main' : 'divider',
          borderRadius: 2,
          p: 4,
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          bgcolor: dragOver ? 'action.hover' : 'transparent',
          '&:hover': {
            borderColor: 'primary.main',
            bgcolor: 'action.hover',
          },
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          onChange={handleInputChange}
          style={{ display: 'none' }}
          aria-label="Select audio or video file"
        />
        <CloudUpload sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
        <Typography variant="body1" sx={{ fontWeight: 500 }}>
          Drag and drop a file here, or click to browse
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Accepted formats: {ACCEPTED_FORMATS_DISPLAY}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Maximum file size: 500 MB
        </Typography>
      </Box>

      {/* File error */}
      {fileError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {fileError}
        </Alert>
      )}

      {/* File preview */}
      {selectedFile && (
        <Paper variant="outlined" sx={{ mt: 2, p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Stack direction="row" spacing={2} alignItems="center">
              <AudioFile color="primary" />
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {selectedFile.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {formatFileSize(selectedFile.size)} -- {selectedFile.type || 'Unknown type'}
                </Typography>
              </Box>
            </Stack>
            <IconButton
              size="small"
              onClick={handleClearFile}
              aria-label="Remove selected file"
              disabled={uploadMutation.isPending}
            >
              <Close fontSize="small" />
            </IconButton>
          </Box>
        </Paper>
      )}

      {/* Upload progress */}
      {uploadMutation.isPending && (
        <Box sx={{ mt: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="body2" color="text.secondary">
              Uploading...
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {uploadProgress}%
            </Typography>
          </Box>
          <LinearProgress variant="determinate" value={uploadProgress} sx={{ height: 6, borderRadius: 3 }} />
        </Box>
      )}

      {/* Language selector and submit */}
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', mt: 2 }}>
        <FormControl sx={{ minWidth: 160 }}>
          <InputLabel id="upload-language-select-label">Language</InputLabel>
          <Select
            labelId="upload-language-select-label"
            label="Language"
            value={uploadLanguage}
            onChange={(e) => setUploadLanguage(e.target.value)}
            aria-label="Select transcription language"
          >
            {LANGUAGE_OPTIONS.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>
                {opt.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button
          variant="contained"
          size="large"
          disabled={!selectedFile || uploadMutation.isPending}
          onClick={() => void handleUploadSubmit()}
          startIcon={<CloudUpload />}
          sx={{ minWidth: 130, height: 56 }}
          aria-label="Upload and transcribe file"
        >
          {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
        </Button>
      </Box>
    </Box>
  );
}

/* ========================================================================
   RECORD AUDIO TAB COMPONENT
   ======================================================================== */

interface RecordAudioTabProps {
  onRecordingUploaded: () => void;
}

function RecordAudioTab({ onRecordingUploaded }: RecordAudioTabProps): JSX.Element {
  const [recordLanguage, setRecordLanguage] = useState<string>('auto');

  const uploadMutation = useUploadTranscription();

  const handleRecordingComplete = useCallback(
    async (file: File): Promise<void> => {
      await uploadMutation.mutateAsync({
        file,
        language: recordLanguage === 'auto' ? undefined : recordLanguage,
      });
      onRecordingUploaded();
    },
    [recordLanguage, uploadMutation, onRecordingUploaded]
  );

  return (
    <Stack spacing={3}>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
        <FormControl sx={{ minWidth: 160 }}>
          <InputLabel id="record-language-select-label">Language</InputLabel>
          <Select
            labelId="record-language-select-label"
            label="Language"
            value={recordLanguage}
            onChange={(e) => setRecordLanguage(e.target.value)}
            aria-label="Select recording language"
            disabled={uploadMutation.isPending}
          >
            {LANGUAGE_OPTIONS.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>
                {opt.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <AudioRecorder
        onRecordingComplete={(file) => void handleRecordingComplete(file)}
        maxDurationSeconds={600}
        disabled={uploadMutation.isPending}
      />

      {uploadMutation.isPending && (
        <Box sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
            Uploading recording for transcription...
          </Typography>
          <LinearProgress />
        </Box>
      )}
    </Stack>
  );
}

/* ========================================================================
   PAGE COMPONENT
   ======================================================================== */

export default function TranscriptionPage(): JSX.Element {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [deleteDialogId, setDeleteDialogId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<number>(0);

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

  const handleUploadComplete = useCallback((): void => {
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
            Transcriptions
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Transcribe audio and video from YouTube, URL, file upload, or microphone recording
          </Typography>
        </Box>
        <Tooltip title="Refresh list">
          <IconButton onClick={handleRefresh} aria-label="Refresh transcriptions">
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Create Form with Tabs */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
            New Transcription
          </Typography>

          <Tabs
            value={activeTab}
            onChange={(_, newValue: number) => setActiveTab(newValue)}
            sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
            aria-label="Transcription source type"
          >
            <Tab label="YouTube / URL" id="tab-url" aria-controls="tabpanel-url" />
            <Tab label="Upload File" id="tab-upload" aria-controls="tabpanel-upload" />
            <Tab label="Record Audio" id="tab-record" aria-controls="tabpanel-record" icon={<Mic />} iconPosition="start" />
          </Tabs>

          {/* Tab 1: YouTube / URL */}
          <Box
            role="tabpanel"
            hidden={activeTab !== 0}
            id="tabpanel-url"
            aria-labelledby="tab-url"
          >
            {activeTab === 0 && (
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
            )}
          </Box>

          {/* Tab 2: Upload File */}
          <Box
            role="tabpanel"
            hidden={activeTab !== 1}
            id="tabpanel-upload"
            aria-labelledby="tab-upload"
          >
            {activeTab === 1 && (
              <FileUploadForm onUploadComplete={handleUploadComplete} />
            )}
          </Box>

          {/* Tab 3: Record Audio */}
          <Box
            role="tabpanel"
            hidden={activeTab !== 2}
            id="tabpanel-record"
            aria-labelledby="tab-record"
          >
            {activeTab === 2 && (
              <RecordAudioTab onRecordingUploaded={handleUploadComplete} />
            )}
          </Box>
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
                Use the form above to transcribe a YouTube video, upload an audio file, or record audio directly.
              </Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table aria-label="Transcriptions table">
                <TableHead>
                  <TableRow>
                    <TableCell>Source</TableCell>
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
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Tooltip title={getSourceLabel(transcription.source_type)}>
                            {getSourceIcon(transcription.source_type)}
                          </Tooltip>
                          <Typography
                            variant="body2"
                            sx={{
                              maxWidth: 300,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {getSourceDisplay(transcription)}
                          </Typography>
                        </Stack>
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
