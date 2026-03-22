/**
 * AudioRecorder Component
 * Browser-based audio recording using the MediaRecorder API.
 */

'use client';

import {
  Box, Button, Card, CardContent, IconButton, Stack, Tooltip, Typography,
} from '@mui/material';
import { Delete, FiberManualRecord, Mic, Stop } from '@mui/icons-material';
import { useCallback, useEffect, useRef, useState } from 'react';

export interface AudioRecorderProps {
  onRecordingComplete: (file: File) => void;
  maxDurationSeconds?: number;
  disabled?: boolean;
}

type RecorderState = 'idle' | 'recording' | 'recorded';

const DEFAULT_MAX_DURATION = 600;
const PREFERRED_MIME_TYPES = [
  'audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4',
];

function getSupportedMimeType(): string {
  for (const mime of PREFERRED_MIME_TYPES) {
    if (MediaRecorder.isTypeSupported(mime)) return mime;
  }
  return '';
}

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function mimeToExtension(mime: string): string {
  if (mime.includes('webm')) return 'webm';
  if (mime.includes('ogg')) return 'ogg';
  if (mime.includes('mp4')) return 'm4a';
  return 'webm';
}

export default function AudioRecorder({
  onRecordingComplete,
  maxDurationSeconds = DEFAULT_MAX_DURATION,
  disabled = false,
}: AudioRecorderProps): JSX.Element {
  const [state, setState] = useState<RecorderState>('idle');
  const [elapsed, setElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const mimeRef = useRef<string>('');
  const blobRef = useRef<Blob | null>(null);

  const stopTimer = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  }, []);

  const releaseStream = useCallback(() => {
    if (streamRef.current) { streamRef.current.getTracks().forEach(t => t.stop()); streamRef.current = null; }
  }, []);

  const revokeAudioUrl = useCallback(() => {
    if (audioUrl) { URL.revokeObjectURL(audioUrl); setAudioUrl(null); }
  }, [audioUrl]);

  useEffect(() => {
    return () => { stopTimer(); releaseStream(); if (audioUrl) URL.revokeObjectURL(audioUrl); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleStart = useCallback(async () => {
    setError(null);
    revokeAudioUrl();
    blobRef.current = null;
    chunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mime = getSupportedMimeType();
      mimeRef.current = mime;
      const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeRef.current || 'audio/webm' });
        blobRef.current = blob;
        setAudioUrl(URL.createObjectURL(blob));
        setState('recorded');
        releaseStream();
        stopTimer();
      };
      recorder.onerror = () => {
        setError('Recording failed. Please try again.');
        setState('idle');
        releaseStream();
        stopTimer();
      };
      recorder.start(1000);
      setElapsed(0);
      setState('recording');
      timerRef.current = setInterval(() => {
        setElapsed(prev => {
          const next = prev + 1;
          if (next >= maxDurationSeconds) recorder.stop();
          return next;
        });
      }, 1000);
    } catch (err) {
      if (err instanceof DOMException && err.name === 'NotAllowedError') {
        setError('Microphone access denied. Please allow microphone access in your browser settings.');
      } else if (err instanceof DOMException && err.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone and try again.');
      } else {
        setError('Failed to access microphone. Please check your browser permissions.');
      }
      setState('idle');
    }
  }, [maxDurationSeconds, releaseStream, revokeAudioUrl, stopTimer]);

  const handleStop = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const handleDiscard = useCallback(() => {
    revokeAudioUrl();
    blobRef.current = null;
    chunksRef.current = [];
    setElapsed(0);
    setState('idle');
  }, [revokeAudioUrl]);

  const handleSubmit = useCallback(() => {
    if (!blobRef.current) return;
    const ext = mimeToExtension(mimeRef.current);
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `recording-${timestamp}.${ext}`;
    const file = new File([blobRef.current], filename, { type: blobRef.current.type });
    onRecordingComplete(file);
  }, [onRecordingComplete]);

  const isRecording = state === 'recording';
  const hasRecording = state === 'recorded';

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={2} alignItems="center">
          <Box
            sx={{
              width: 80, height: 80, borderRadius: '50%',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              bgcolor: isRecording ? 'error.light' : 'action.hover',
              transition: 'background-color 0.3s',
              animation: isRecording ? 'pulse 1.5s infinite' : 'none',
              '@keyframes pulse': {
                '0%': { transform: 'scale(1)', opacity: 1 },
                '50%': { transform: 'scale(1.05)', opacity: 0.8 },
                '100%': { transform: 'scale(1)', opacity: 1 },
              },
            }}
          >
            {isRecording ? (
              <FiberManualRecord sx={{ fontSize: 40, color: 'error.contrastText' }} />
            ) : (
              <Mic sx={{ fontSize: 40, color: 'text.secondary' }} />
            )}
          </Box>

          <Typography variant="h5" sx={{ fontFamily: 'monospace', fontWeight: 600 }} aria-live="polite">
            {formatElapsed(elapsed)}
          </Typography>

          {isRecording && (
            <Typography variant="caption" color="text.secondary">
              Max duration: {formatElapsed(maxDurationSeconds)}
            </Typography>
          )}

          <Stack direction="row" spacing={2} alignItems="center">
            {state === 'idle' && (
              <Button variant="contained" color="error" startIcon={<Mic />}
                onClick={() => void handleStart()} disabled={disabled} size="large"
                aria-label="Start recording">
                Start Recording
              </Button>
            )}
            {isRecording && (
              <Button variant="contained" color="inherit" startIcon={<Stop />}
                onClick={handleStop} size="large" aria-label="Stop recording">
                Stop
              </Button>
            )}
            {hasRecording && (
              <>
                <Tooltip title="Discard recording">
                  <IconButton onClick={handleDiscard} color="error"
                    aria-label="Discard recording" disabled={disabled}>
                    <Delete />
                  </IconButton>
                </Tooltip>
                <Button variant="contained" color="primary" onClick={handleSubmit}
                  disabled={disabled} size="large" aria-label="Submit recording for transcription">
                  {disabled ? 'Uploading...' : 'Transcribe Recording'}
                </Button>
              </>
            )}
          </Stack>

          {hasRecording && audioUrl && (
            <Box sx={{ width: '100%', maxWidth: 400 }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                Preview
              </Typography>
              {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
              <audio controls src={audioUrl} style={{ width: '100%' }} />
            </Box>
          )}

          {error && (
            <Typography variant="body2" color="error" role="alert">
              {error}
            </Typography>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
