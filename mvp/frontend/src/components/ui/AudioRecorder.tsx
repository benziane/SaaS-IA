/**
 * AudioRecorder Component
 * Browser-based audio recording using the MediaRecorder API.
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Trash2, Circle, Mic, Square } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/lib/design-hub/components/Button';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';

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
}: AudioRecorderProps) {
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
    <Card className="border border-[var(--border)]">
      <CardContent className="p-6">
        <div className="flex flex-col items-center gap-4">
          <div
            className={`w-20 h-20 rounded-full flex items-center justify-center transition-colors duration-300 ${
              isRecording
                ? 'bg-red-500/20 animate-pulse'
                : 'bg-[var(--bg-elevated)]'
            }`}
          >
            {isRecording ? (
              <Circle className="h-10 w-10 text-red-500 fill-red-500" />
            ) : (
              <Mic className="h-10 w-10 text-[var(--text-low)]" />
            )}
          </div>

          <h3 className="text-2xl font-semibold font-mono" aria-live="polite">
            {formatElapsed(elapsed)}
          </h3>

          {isRecording && (
            <span className="text-xs text-[var(--text-low)]">
              Max duration: {formatElapsed(maxDurationSeconds)}
            </span>
          )}

          <div className="flex items-center gap-4">
            {state === 'idle' && (
              <Button
                variant="destructive"
                size="lg"
                onClick={() => void handleStart()}
                disabled={disabled}
                aria-label="Start recording"
                className="gap-2"
              >
                <Mic className="h-5 w-5" />
                Start Recording
              </Button>
            )}
            {isRecording && (
              <Button
                variant="secondary"
                size="lg"
                onClick={handleStop}
                aria-label="Stop recording"
                className="gap-2"
              >
                <Square className="h-5 w-5" />
                Stop
              </Button>
            )}
            {hasRecording && (
              <>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleDiscard}
                        disabled={disabled}
                        aria-label="Discard recording"
                        className="text-red-500 hover:text-red-600"
                      >
                        <Trash2 className="h-5 w-5" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Discard recording</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                <Button
                  size="lg"
                  onClick={handleSubmit}
                  disabled={disabled}
                  aria-label="Submit recording for transcription"
                >
                  {disabled ? 'Uploading...' : 'Transcribe Recording'}
                </Button>
              </>
            )}
          </div>

          {hasRecording && audioUrl && (
            <div className="w-full max-w-[400px]">
              <span className="text-xs text-[var(--text-low)] mb-1 block">
                Preview
              </span>
              {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
              <audio controls src={audioUrl} style={{ width: '100%' }} />
            </div>
          )}

          {error && (
            <p className="text-sm text-red-400" role="alert">
              {error}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
