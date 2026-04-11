/**
 * Transcription Page
 * Multi-source transcription management with YouTube/URL input, file upload,
 * result display, export, and language selection.
 */

'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import {
  FileAudio, Sparkles, MessageSquare, X, CloudUpload, Copy, Trash2,
  Download, ChevronDown, Link as LinkIcon, Mic, RefreshCw, Square,
  Subtitles, Eye,
} from 'lucide-react';
import { useCallback, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Controller, useForm } from 'react-hook-form';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Separator } from '@/lib/design-hub/components/Separator';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/lib/design-hub/components/Tabs';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '@/lib/design-hub/components/Dialog';

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

function getStatusVariant(
  status: TranscriptionStatus
): 'secondary' | 'default' | 'success' | 'destructive' {
  switch (status) {
    case TranscriptionStatus.PENDING:
      return 'secondary';
    case TranscriptionStatus.PROCESSING:
      return 'default';
    case TranscriptionStatus.COMPLETED:
      return 'success';
    case TranscriptionStatus.FAILED:
      return 'destructive';
    default:
      return 'secondary';
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

function getSourceIcon(sourceType: TranscriptionSourceType | undefined) {
  switch (sourceType) {
    case 'upload':
      return <FileAudio className="h-4 w-4 text-blue-400" />;
    case 'url':
      return <LinkIcon className="h-4 w-4 text-amber-400" />;
    case 'youtube':
    default:
      return <Subtitles className="h-4 w-4 text-red-400" />;
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

function ExportButtons({ transcription }: ExportButtonsProps) {
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
    <div className="flex gap-2">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button size="sm" variant="outline" onClick={() => void handleCopy()}>
            <Copy className="h-3 w-3 mr-1" /> {copied ? 'Copied' : 'Copy'}
          </Button>
        </TooltipTrigger>
        <TooltipContent>{copied ? 'Copied!' : 'Copy to clipboard'}</TooltipContent>
      </Tooltip>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button size="sm" variant="outline" onClick={handleDownloadTxt}>
            <Download className="h-3 w-3 mr-1" /> TXT
          </Button>
        </TooltipTrigger>
        <TooltipContent>Download as plain text file</TooltipContent>
      </Tooltip>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button size="sm" variant="outline" onClick={handleDownloadSrt}>
            <Subtitles className="h-3 w-3 mr-1" /> SRT
          </Button>
        </TooltipTrigger>
        <TooltipContent>Download as SRT subtitle file</TooltipContent>
      </Tooltip>
    </div>
  );
}

interface TranscriptionDetailProps {
  transcription: Transcription;
  onClose: () => void;
}

function TranscriptionDetail({ transcription, onClose }: TranscriptionDetailProps) {
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
    <div className="surface-card p-6 animate-enter">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-sm font-semibold text-[var(--text-high)] flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-[var(--accent)]" />
          Transcription Details
        </h3>
          <button type="button" onClick={onClose} className="p-1 text-[var(--text-low)] hover:text-[var(--text-high)] transition-colors" aria-label="Close details">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Metadata row */}
        <div className="flex flex-wrap gap-6 mb-4">
          <div>
            <span className="text-xs text-[var(--text-low)]">Status</span>
            <div className="mt-0.5">
              <Badge variant={getStatusVariant(transcription.status)}>{transcription.status}</Badge>
            </div>
          </div>
          <div>
            <span className="text-xs text-[var(--text-low)]">Language</span>
            <p className="text-sm text-[var(--text-mid)]">{getLanguageLabel(transcription.language)}</p>
          </div>
          <div>
            <span className="text-xs text-[var(--text-low)]">Duration</span>
            <p className="text-sm text-[var(--text-mid)]">{formatDuration(transcription.duration_seconds)}</p>
          </div>
          {transcription.confidence !== null && (
            <div className="min-w-[160px]">
              <span className="text-xs text-[var(--text-low)]">
                Confidence: {(transcription.confidence * 100).toFixed(1)}%
              </span>
              <Progress
                value={transcription.confidence * 100}
                className="mt-1 h-1.5"
              />
            </div>
          )}
          <div>
            <span className="text-xs text-[var(--text-low)]">Created</span>
            <p className="text-sm text-[var(--text-mid)]">{formatDate(transcription.created_at)}</p>
          </div>
          {transcription.completed_at && (
            <div>
              <span className="text-xs text-[var(--text-low)]">Completed</span>
              <p className="text-sm text-[var(--text-mid)]">{formatDate(transcription.completed_at)}</p>
            </div>
          )}
        </div>

        <Separator className="mb-4" />

        {/* Error display */}
        {transcription.error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{transcription.error}</AlertDescription>
          </Alert>
        )}

        {/* Processing indicator */}
        {transcription.status === TranscriptionStatus.PROCESSING && (
          <div className="mb-4">
            <p className="text-sm text-[var(--text-mid)] mb-2">
              Transcription in progress...
            </p>
            <Progress />
          </div>
        )}

        {/* Transcription text */}
        {transcription.text && (
          <div>
            <div className="flex justify-between items-center mb-2">
              <h4 className="text-sm font-semibold text-[var(--text-high)]">
                {streamDone ? 'Original Transcription' : 'Transcription Text'}
              </h4>
              <div className="flex gap-2 items-center">
                <ExportButtons transcription={transcription} />
                {transcription.status === TranscriptionStatus.COMPLETED && !isStreaming && (
                  <>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => router.push(`/chat?transcription_id=${transcription.id}`)}
                        >
                          <MessageSquare className="h-3 w-3 mr-1" /> Chat about this
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Chat with AI about this transcription</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleImproveWithAI}
                        >
                          <Sparkles className="h-3 w-3 mr-1" /> Improve with AI
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Improve transcription text using AI</TooltipContent>
                    </Tooltip>
                  </>
                )}
                {isStreaming && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={stopStream}
                      >
                        <Square className="h-3 w-3 mr-1" /> Stop
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Stop AI streaming</TooltipContent>
                  </Tooltip>
                )}
              </div>
            </div>

            {showOriginalText && (
              <div className="rounded-md border border-[var(--border)] bg-[var(--bg-elevated)] p-4 max-h-[400px] overflow-auto">
                <p className="text-sm text-[var(--text-mid)] whitespace-pre-wrap break-words leading-7">
                  {transcription.text}
                </p>
              </div>
            )}
            {showOriginalText && (
              <span className="text-xs text-[var(--text-low)] mt-2 block">
                {transcription.text.split(/\s+/).length} words
              </span>
            )}

            {/* AI-Improved Text Section */}
            {showImprovedSection && (
              <div className="mt-6">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="text-sm font-semibold text-[var(--text-high)]">
                    AI-Improved Text
                  </h4>
                  {streamDone && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => void handleCopyImproved()}
                        >
                          <Copy className="h-3 w-3 mr-1" /> {copiedImproved ? 'Copied' : 'Copy improved text'}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>{copiedImproved ? 'Copied!' : 'Copy improved text to clipboard'}</TooltipContent>
                    </Tooltip>
                  )}
                </div>

                {streamError && (
                  <Alert variant="destructive" className="mb-4">
                    <AlertDescription>{streamError}</AlertDescription>
                  </Alert>
                )}

                <StreamingText
                  text={improvedText}
                  isStreaming={isStreaming}
                  provider={streamProvider}
                  tokenCount={streamTokenCount}
                />
              </div>
            )}
          </div>
        )}
    </div>
  );
}

/* ========================================================================
   FILE UPLOAD TAB COMPONENT
   ======================================================================== */

interface FileUploadFormProps {
  onUploadComplete: () => void;
}

function FileUploadForm({ onUploadComplete }: FileUploadFormProps) {
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
    <div>
      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
          ${dragOver ? 'border-[var(--accent)] bg-[var(--bg-elevated)]' : fileError ? 'border-red-500' : 'border-[var(--border)] hover:border-[var(--accent)] hover:bg-[var(--bg-elevated)]'}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          onChange={handleInputChange}
          className="hidden"
          aria-label="Select audio or video file"
        />
        <CloudUpload className="h-12 w-12 text-[var(--text-low)] mx-auto mb-2" />
        <p className="font-medium text-[var(--text-high)]">
          Drag and drop a file here, or click to browse
        </p>
        <p className="text-sm text-[var(--text-mid)] mt-2">
          Accepted formats: {ACCEPTED_FORMATS_DISPLAY}
        </p>
        <p className="text-xs text-[var(--text-low)]">
          Maximum file size: 500 MB
        </p>
      </div>

      {/* File error */}
      {fileError && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{fileError}</AlertDescription>
        </Alert>
      )}

      {/* File preview */}
      {selectedFile && (
        <div className="rounded-md border border-[var(--border)] mt-4 p-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <FileAudio className="h-5 w-5 text-[var(--accent)]" />
              <div>
                <p className="text-sm font-semibold text-[var(--text-high)]">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-[var(--text-low)]">
                  {formatFileSize(selectedFile.size)} -- {selectedFile.type || 'Unknown type'}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleClearFile}
              aria-label="Remove selected file"
              disabled={uploadMutation.isPending}
              className="p-1 text-[var(--text-low)] hover:text-[var(--text-high)] disabled:opacity-50 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Upload progress */}
      {uploadMutation.isPending && (
        <div className="mt-4">
          <div className="flex justify-between mb-1">
            <span className="text-sm text-[var(--text-mid)]">Uploading...</span>
            <span className="text-sm text-[var(--text-mid)]">{uploadProgress}%</span>
          </div>
          <Progress value={uploadProgress} className="h-1.5" />
        </div>
      )}

      {/* Language selector and submit */}
      <div className="flex gap-4 items-start mt-4">
        <div className="w-[160px]">
          <label className="block text-xs text-[var(--text-low)] mb-1">Language</label>
          <Select value={uploadLanguage} onValueChange={setUploadLanguage}>
            <SelectTrigger aria-label="Select transcription language">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LANGUAGE_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="pt-5">
          <Button
            size="lg"
            disabled={!selectedFile || uploadMutation.isPending}
            onClick={() => void handleUploadSubmit()}
            aria-label="Upload and transcribe file"
          >
            <CloudUpload className="h-4 w-4 mr-2" />
            {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ========================================================================
   RECORD AUDIO TAB COMPONENT
   ======================================================================== */

interface RecordAudioTabProps {
  onRecordingUploaded: () => void;
}

function RecordAudioTab({ onRecordingUploaded }: RecordAudioTabProps) {
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
    <div className="flex flex-col gap-6">
      <div className="w-[160px]">
        <label className="block text-xs text-[var(--text-low)] mb-1">Language</label>
        <Select
          value={recordLanguage}
          onValueChange={setRecordLanguage}
          disabled={uploadMutation.isPending}
        >
          <SelectTrigger aria-label="Select recording language">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {LANGUAGE_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <AudioRecorder
        onRecordingComplete={(file) => void handleRecordingComplete(file)}
        maxDurationSeconds={600}
        disabled={uploadMutation.isPending}
      />

      {uploadMutation.isPending && (
        <div>
          <p className="text-sm text-[var(--text-mid)] mb-1">
            Uploading recording for transcription...
          </p>
          <Progress />
        </div>
      )}
    </div>
  );
}

/* ========================================================================
   PAGE COMPONENT
   ======================================================================== */

export default function TranscriptionPage() {
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
    <TooltipProvider>
      <div className="p-5 space-y-5 animate-enter">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
              <FileAudio className="h-5 w-5 text-[var(--accent)]" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-[var(--text-high)]">Transcriptions</h1>
              <p className="text-xs text-[var(--text-mid)]">
                YouTube, URL, file upload, or microphone recording
              </p>
            </div>
          </div>
          <Tooltip>
            <TooltipTrigger asChild>
              <button type="button" onClick={handleRefresh} className="p-2 text-[var(--text-mid)] hover:text-[var(--text-high)] hover:bg-[var(--bg-elevated)] rounded-md transition-colors" aria-label="Refresh transcriptions">
                <RefreshCw className="h-5 w-5" />
              </button>
            </TooltipTrigger>
            <TooltipContent>Refresh list</TooltipContent>
          </Tooltip>
        </div>

        {/* Create Form with Tabs */}
        <div className="surface-card p-6">
          <h3 className="text-sm font-semibold text-[var(--text-high)] mb-4 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-[var(--accent)]" />
            New Transcription
          </h3>

            <Tabs defaultValue="url">
              <TabsList className="mb-6">
                <TabsTrigger value="url">YouTube / URL</TabsTrigger>
                <TabsTrigger value="upload">Upload File</TabsTrigger>
                <TabsTrigger value="record" className="flex items-center gap-1.5">
                  <Mic className="h-3.5 w-3.5" /> Record Audio
                </TabsTrigger>
              </TabsList>

              {/* Tab 1: YouTube / URL */}
              <TabsContent value="url">
                <form onSubmit={handleSubmit(onSubmit)}>
                  <div className="flex gap-4 items-start">
                    <Controller
                      name="video_url"
                      control={control}
                      render={({ field }) => (
                        <div className="flex-1">
                          <Input
                            {...field}
                            placeholder="https://www.youtube.com/watch?v=..."
                            className={errors.video_url ? 'border-red-500' : ''}
                            aria-label="YouTube video URL"
                            aria-required="true"
                            aria-invalid={!!errors.video_url}
                          />
                          {errors.video_url && (
                            <p className="mt-1 text-xs text-red-400">{errors.video_url.message}</p>
                          )}
                        </div>
                      )}
                    />
                    <Controller
                      name="language"
                      control={control}
                      render={({ field }) => (
                        <div className="w-[160px]">
                          <Select
                            value={field.value ?? 'auto'}
                            onValueChange={field.onChange}
                          >
                            <SelectTrigger aria-label="Select transcription language">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {LANGUAGE_OPTIONS.map(opt => (
                                <SelectItem key={opt.value} value={opt.value}>
                                  {opt.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                    />
                    <Button
                      type="submit"
                      size="lg"
                      disabled={isSubmitting || createMutation.isPending}
                      aria-label="Start transcription"
                    >
                      {isSubmitting || createMutation.isPending ? 'Starting...' : 'Transcribe'}
                    </Button>
                  </div>
                </form>
              </TabsContent>

              {/* Tab 2: Upload File */}
              <TabsContent value="upload">
                <FileUploadForm onUploadComplete={handleUploadComplete} />
              </TabsContent>

              {/* Tab 3: Record Audio */}
              <TabsContent value="record">
                <RecordAudioTab onRecordingUploaded={handleUploadComplete} />
              </TabsContent>
            </Tabs>
        </div>

        {/* Transcriptions Table */}
        <div className="surface-card p-6">
          <h3 className="text-sm font-semibold text-[var(--text-high)] mb-4 flex items-center gap-2">
            <Subtitles className="h-4 w-4 text-[var(--accent)]" />
            Your Transcriptions
          </h3>

            {isLoading ? (
              <div className="py-8 text-center">
                <Progress className="mb-4" />
                <p className="text-sm text-[var(--text-mid)]">
                  Loading transcriptions...
                </p>
              </div>
            ) : !data || data.items.length === 0 ? (
              <div className="py-12 text-center">
                <Subtitles className="h-12 w-12 text-[var(--text-low)] mx-auto mb-4" />
                <h4 className="text-lg text-[var(--text-mid)] mb-2">
                  No transcriptions yet
                </h4>
                <p className="text-sm text-[var(--text-mid)]">
                  Use the form above to transcribe a YouTube video, upload an audio file, or record audio directly.
                </p>
              </div>
            ) : (
              <div className="rounded-md border border-[var(--border)] overflow-hidden">
                <table className="w-full text-sm" aria-label="Transcriptions table">
                  <thead>
                    <tr className="border-b border-[var(--border)] bg-[var(--bg-elevated)]">
                      <th className="text-left p-3 font-medium text-[var(--text-mid)]">Source</th>
                      <th className="text-left p-3 font-medium text-[var(--text-mid)]">Status</th>
                      <th className="text-left p-3 font-medium text-[var(--text-mid)]">Language</th>
                      <th className="text-left p-3 font-medium text-[var(--text-mid)]">Date</th>
                      <th className="text-right p-3 font-medium text-[var(--text-mid)]">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map(transcription => (
                      <tr
                        key={transcription.id}
                        className={`border-b border-[var(--border)] hover:bg-[var(--bg-elevated)] cursor-pointer transition-colors ${selectedId === transcription.id ? 'bg-[var(--bg-elevated)]' : ''}`}
                      >
                        <td
                          className="p-3"
                          onClick={() =>
                            setSelectedId(prev =>
                              prev === transcription.id ? null : transcription.id
                            )
                          }
                        >
                          <div className="flex items-center gap-2">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <span>{getSourceIcon(transcription.source_type)}</span>
                              </TooltipTrigger>
                              <TooltipContent>{getSourceLabel(transcription.source_type)}</TooltipContent>
                            </Tooltip>
                            <span className="max-w-[300px] overflow-hidden text-ellipsis whitespace-nowrap text-[var(--text-mid)]">
                              {getSourceDisplay(transcription)}
                            </span>
                          </div>
                        </td>
                        <td className="p-3">
                          <Badge
                            variant={getStatusVariant(transcription.status)}
                            className={transcription.status === TranscriptionStatus.PROCESSING ? 'border border-[var(--accent)]/30' : ''}
                          >
                            {transcription.status}
                          </Badge>
                        </td>
                        <td className="p-3 text-[var(--text-mid)]">
                          {getLanguageLabel(transcription.language)}
                        </td>
                        <td className="p-3 text-[var(--text-low)]">
                          {formatDate(transcription.created_at)}
                        </td>
                        <td className="p-3">
                          <div className="flex gap-1 justify-end">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  onClick={() =>
                                    setSelectedId(prev =>
                                      prev === transcription.id ? null : transcription.id
                                    )
                                  }
                                  className={`p-1.5 rounded-md transition-colors ${selectedId === transcription.id ? 'text-[var(--accent)] bg-[var(--accent)]/10' : 'text-[var(--text-low)] hover:text-[var(--text-high)] hover:bg-[var(--bg-elevated)]'}`}
                                  aria-label="View transcription details"
                                >
                                  {selectedId === transcription.id ? (
                                    <ChevronDown className="h-4 w-4" />
                                  ) : (
                                    <Eye className="h-4 w-4" />
                                  )}
                                </button>
                              </TooltipTrigger>
                              <TooltipContent>View details</TooltipContent>
                            </Tooltip>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  type="button"
                                  onClick={() => setDeleteDialogId(transcription.id)}
                                  disabled={deleteMutation.isPending}
                                  className="p-1.5 rounded-md text-red-400 hover:text-red-300 hover:bg-red-500/10 disabled:opacity-50 transition-colors"
                                  aria-label="Delete transcription"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent>Delete</TooltipContent>
                            </Tooltip>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
        </div>

        {/* Selected Transcription Detail Panel */}
        {selectedTranscription && (
          <TranscriptionDetail
            transcription={selectedTranscription}
            onClose={() => setSelectedId(null)}
          />
        )}

        {/* Delete Confirmation Dialog */}
        <Dialog open={!!deleteDialogId} onOpenChange={(open) => !open && setDeleteDialogId(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Transcription</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this transcription? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="ghost" onClick={() => setDeleteDialogId(null)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => void handleDeleteConfirm()}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
