'use client';

/**
 * Transcription Debug Page - Grade S++
 * Real-time debugging interface for YouTube transcription
 */

import { useState, useEffect, useRef } from 'react';
import {
  Play, CheckCircle2, AlertCircle, Clock, Bug, Download, Volume2,
  Copy, RefreshCw, FlaskConical, X, Loader2,
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Separator } from '@/lib/design-hub/components/Separator';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/lib/design-hub/components/Dialog';
import apiClient, { extractErrorMessage } from '@/lib/apiClient';

/* ========================================================================
   URL UTILITIES
   ======================================================================== */

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004';
}

function getWsBaseUrl(): string {
  const base = getApiBaseUrl();
  return base.replace(/^http/, 'ws');
}

/* ========================================================================
   TYPES
   ======================================================================== */

interface DebugStep {
  step: string;
  status: string;
  timestamp: string;
  duration_seconds: number;
  data?: any;
  error?: string;
}

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function TranscriptionDebugPage() {
  // State
  const [videoUrl, setVideoUrl] = useState('https://youtu.be/C49V1SArjtY');
  const [jobId, setJobId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [debugSteps, setDebugSteps] = useState<DebugStep[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [finalResult, setFinalResult] = useState<any>(null);

  // Backend test state
  const [isBackendTestRunning, setIsBackendTestRunning] = useState(false);
  const [backendTestResult, setBackendTestResult] = useState<any>(null);
  const [showBackendTestModal, setShowBackendTestModal] = useState(false);

  // AI Content Restructuring state
  const [isReformattingGemini, setIsReformattingGemini] = useState(false);
  const [isReformattingGroq, setIsReformattingGroq] = useState(false);
  const [geminiResult, setGeminiResult] = useState<string | null>(null);
  const [groqResult, setGroqResult] = useState<string | null>(null);

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const stepsEndRef = useRef<HTMLDivElement>(null);

  /* ========================================================================
     EFFECTS
     ======================================================================== */

  useEffect(() => {
    stepsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [debugSteps]);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  /* ========================================================================
     WEBSOCKET CONNECTION
     ======================================================================== */

  const connectWebSocket = (jobId: string) => {
    const wsUrl = `${getWsBaseUrl()}/api/transcription/debug/${jobId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[WebSocket] Connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('[WebSocket] Message:', message);

      if (message.type === 'debug_step') {
        setDebugSteps((prev) => {
          const existingIndex = prev.findIndex(s => s.step === message.step.step);

          if (existingIndex !== -1) {
            const updated = [...prev];
            updated[existingIndex] = message.step;
            return updated;
          } else {
            return [...prev, message.step];
          }
        });
      } else if (message.type === 'connected') {
        console.log('[WebSocket] Connection confirmed');
      }
    };

    ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
    };

    ws.onclose = () => {
      console.log('[WebSocket] Disconnected');
    };

    wsRef.current = ws;

    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  };

  /* ========================================================================
     HANDLERS
     ======================================================================== */

  const startTranscription = async () => {
    if (!videoUrl.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    setError(null);
    setDebugSteps([]);
    setFinalResult(null);
    setIsProcessing(true);

    try {
      const tempJobId = `debug-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      setJobId(tempJobId);

      console.log('[Debug] Connecting WebSocket first...');
      connectWebSocket(tempJobId);

      await new Promise((resolve) => setTimeout(resolve, 1000));

      console.log('[Debug] Starting transcription with job_id:', tempJobId);
      const response = await apiClient.post(`/api/transcription/debug/transcribe/${tempJobId}`, {
        video_url: videoUrl
      }, {
        timeout: 300000
      });

      const result = response.data;
      console.log('[Debug] Transcription complete:', result);

      setFinalResult(result);
      setIsProcessing(false);

      if (wsRef.current) {
        wsRef.current.close();
      }

    } catch (err: any) {
      console.error('[Debug] Error:', err);
      setError(err.message || 'An error occurred');
      setIsProcessing(false);

      if (wsRef.current) {
        wsRef.current.close();
      }
    }
  };

  const handleReset = () => {
    setVideoUrl('');
    setJobId(null);
    setDebugSteps([]);
    setFinalResult(null);
    setError(null);
    setIsProcessing(false);
    if (wsRef.current) {
      wsRef.current.close();
    }
  };

  const runBackendTest = async () => {
    setIsBackendTestRunning(true);
    setBackendTestResult(null);
    setError(null);

    try {
      const response = await apiClient.post('/api/transcription/debug/run-backend-test');
      const result = response.data;
      setBackendTestResult(result);
      setShowBackendTestModal(true);

    } catch (err: any) {
      console.error('[Backend Test] Error:', err);
      setError(err.message || 'Failed to run backend test');
    } finally {
      setIsBackendTestRunning(false);
    }
  };

  const copyJobId = () => {
    if (jobId) {
      navigator.clipboard.writeText(jobId);
    }
  };

  const reformatWithAI = async (provider: 'gemini' | 'groq') => {
    if (!finalResult?.text) {
      setError('No transcription text available to reformat');
      return;
    }

    const setLoading = provider === 'gemini' ? setIsReformattingGemini : setIsReformattingGroq;
    const setResult = provider === 'gemini' ? setGeminiResult : setGroqResult;

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post('/api/ai-assistant/process-text', {
        text: finalResult.text,
        task: 'format_text',
        provider: provider,
        language: finalResult.language_code || 'auto'
      });

      setResult(response.data.processed_text);

    } catch (err: any) {
      console.error(`[${provider.toUpperCase()}] Reformat error:`, err);
      const errorMessage = extractErrorMessage(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const copyAllLogs = () => {
    const logs = {
      jobId,
      videoUrl,
      timestamp: new Date().toISOString(),
      totalSteps: debugSteps.length,
      isProcessing,
      hasError: !!error,
      error,
      steps: debugSteps.map((step, index) => ({
        stepNumber: index + 1,
        stepName: step.step,
        status: step.status,
        timestamp: step.timestamp,
        durationSeconds: step.duration_seconds,
        data: step.data,
        error: step.error,
      })),
      finalResult: finalResult ? {
        text: finalResult.text,
        confidence: finalResult.confidence,
        durationSeconds: finalResult.duration_seconds,
        jobId: finalResult.job_id,
        audioAvailable: finalResult.audio_available,
        textLength: finalResult.text?.length || 0,
        wordCount: finalResult.text?.split(/\s+/).length || 0,
      } : null,
    };

    const logsJson = JSON.stringify(logs, null, 2);
    navigator.clipboard.writeText(logsJson);
    alert('All logs copied to clipboard! You can now paste them to share.');
  };

  /* ========================================================================
     RENDER HELPERS
     ======================================================================== */

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircle2 className="h-5 w-5 text-green-400" />;
      case 'ERROR':
      case 'FAILED':
        return <AlertCircle className="h-5 w-5 text-red-400" />;
      case 'IN_PROGRESS':
        return <Loader2 className="h-5 w-5 animate-spin text-[var(--accent)]" />;
      default:
        return <Clock className="h-5 w-5 text-[var(--text-low)]" />;
    }
  };

  const getStatusVariant = (status: string): 'success' | 'destructive' | 'default' | 'secondary' => {
    switch (status) {
      case 'SUCCESS':
        return 'success';
      case 'ERROR':
      case 'FAILED':
        return 'destructive';
      case 'IN_PROGRESS':
        return 'default';
      default:
        return 'secondary';
    }
  };

  const getBorderColor = (status: string): string => {
    switch (status) {
      case 'SUCCESS': return 'border-l-green-500';
      case 'ERROR': case 'FAILED': return 'border-l-red-500';
      case 'IN_PROGRESS': return 'border-l-blue-500';
      default: return 'border-l-[var(--border)]';
    }
  };

  /* ========================================================================
     RENDER
     ======================================================================== */

  return (
    <TooltipProvider>
      <div className="p-5 space-y-5 animate-enter">
        {/* Page Header + Controls Card */}
        <div className="surface-card p-5">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
                <Bug className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-[var(--text-high)]">Transcription Debug</h1>
                <p className="text-xs text-[var(--text-mid)]">Transcription debugging and diagnostics</p>
              </div>
            </div>
            {debugSteps.length > 0 && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={handleReset}
                    className="p-2 text-[var(--accent)] hover:bg-[var(--bg-elevated)] rounded-md transition-colors"
                    aria-label="Reset"
                  >
                    <RefreshCw className="h-5 w-5" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>Reset</TooltipContent>
              </Tooltip>
            )}
          </div>

          <div className="flex flex-col gap-4">
            <div>
              <label className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">
                YouTube URL
              </label>
              <Input
                placeholder="https://youtu.be/..."
                value={videoUrl}
                onChange={(e) => setVideoUrl(e.target.value)}
                disabled={isProcessing}
              />
              <p className="mt-1 text-xs text-[var(--text-low)]">
                Enter a YouTube video URL to start debugging
              </p>
            </div>

            <Button
              size="lg"
              className="w-full"
              onClick={startTranscription}
              disabled={isProcessing || !videoUrl.trim()}
            >
              {isProcessing ? (
                <><Loader2 className="h-5 w-5 animate-spin mr-2" /> Processing...</>
              ) : (
                <><Play className="h-5 w-5 mr-2" /> Start Debug Transcription</>
              )}
            </Button>

            <div className="relative flex items-center">
              <Separator className="flex-1" />
              <Badge variant="outline" className="mx-3">OR</Badge>
              <Separator className="flex-1" />
            </div>

            <Button
              variant="outline"
              size="lg"
              className="w-full"
              onClick={runBackendTest}
              disabled={isBackendTestRunning || isProcessing}
            >
              {isBackendTestRunning ? (
                <><Loader2 className="h-5 w-5 animate-spin mr-2" /> Running Backend Test...</>
              ) : (
                <><FlaskConical className="h-5 w-5 mr-2" /> Run Full Backend Test (Python)</>
              )}
            </Button>

            <Alert variant="info">
              <FlaskConical className="h-4 w-4" />
              <AlertDescription>
                <strong>Backend Test:</strong> Runs the complete transcription pipeline in Python (backend-only).
                This test uses the default video and displays the final result with AI improvements.
              </AlertDescription>
            </Alert>

            {jobId && (
              <Alert variant="info">
                <div className="flex items-center justify-between w-full">
                  <span><strong>Job ID:</strong> {jobId}</span>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button type="button" onClick={copyJobId} className="p-1 text-[var(--text-mid)] hover:text-[var(--text-high)] transition-colors" aria-label="Copy Job ID">
                        <Copy className="h-4 w-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent>Copy Job ID</TooltipContent>
                  </Tooltip>
                </div>
              </Alert>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertDescription className="flex items-center justify-between">
                  {error}
                  <button type="button" onClick={() => setError(null)} className="p-1 text-red-400 hover:text-red-300" aria-label="Dismiss error">
                    <X className="h-4 w-4" />
                  </button>
                </AlertDescription>
              </Alert>
            )}
          </div>

          {isProcessing && <Progress value={undefined} className="h-1 mt-4" />}
        </div>

        {/* Debug Logs Export */}
        {debugSteps.length > 0 && (
          <div className="surface-card p-5 bg-[var(--accent)]/5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Copy className="h-5 w-5 text-[var(--accent)]" />
                <div>
                  <p className="text-base font-semibold text-[var(--text-high)]">Export Debug Logs</p>
                  <p className="text-xs text-[var(--text-mid)]">Copy all logs to share for debugging</p>
                </div>
              </div>
              <Button onClick={copyAllLogs}>
                <Copy className="h-4 w-4 mr-2" /> Copy All Logs
              </Button>
            </div>
            <Alert variant="info">
              <AlertDescription>
                Click &quot;Copy All Logs&quot; to copy all transcription data (steps, errors, results) to your clipboard in JSON format.
                You can then paste it to share for debugging.
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Debug Steps */}
        {debugSteps.length > 0 && (
          <div className="surface-card p-5">
            <div className="mb-4">
              <p className="text-base font-semibold text-[var(--text-high)]">Debug Steps ({debugSteps.length})</p>
              <p className="text-xs text-[var(--text-mid)]">Real-time transcription process</p>
            </div>
            <div className="max-h-[600px] overflow-y-auto">
              <div className="flex flex-col gap-4">
                {debugSteps.map((step, index) => (
                  <div
                    key={index}
                    className={`rounded-lg border border-[var(--border)] border-l-4 ${getBorderColor(step.status)} bg-[var(--bg-surface)] p-4`}
                  >
                    <div className="flex flex-col gap-2">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(step.status)}
                          <span className="font-semibold text-[var(--text-high)]">{step.step}</span>
                          <Badge variant={getStatusVariant(step.status)}>{step.status}</Badge>
                        </div>
                        <Badge variant="outline">{step.duration_seconds.toFixed(2)}s</Badge>
                      </div>

                      {step.data && Object.keys(step.data).length > 0 && (
                        <>
                          <div className="rounded-md border border-[var(--border)] bg-[var(--bg-elevated)] p-3 max-h-[300px] overflow-y-auto">
                            <span className="text-xs font-semibold text-[var(--text-low)]">Data:</span>
                            <pre className="text-xs overflow-auto mt-2 whitespace-pre-wrap break-words text-[var(--text-mid)]">
                              {JSON.stringify(step.data, null, 2)}
                            </pre>
                          </div>

                          {/* Audio download buttons for step 2 */}
                          {step.step.includes('AUDIO DOWNLOAD') &&
                           step.status === 'SUCCESS' &&
                           step.data['📤 OUTPUT']?.audio_download_url && (
                            <div className="flex items-center gap-2 flex-wrap">
                              <Button
                                size="sm"
                                onClick={async () => {
                                  try {
                                    const token = localStorage.getItem('auth_token');
                                    const url = `${getApiBaseUrl()}${step.data['📤 OUTPUT'].audio_download_url}`;
                                    const response = await fetch(url, {
                                      headers: { 'Authorization': `Bearer ${token}` }
                                    });
                                    if (!response.ok) throw new Error('Failed to load audio');
                                    const blob = await response.blob();
                                    const blobUrl = URL.createObjectURL(blob);
                                    window.open(blobUrl, '_blank');
                                  } catch (err: any) {
                                    alert('Failed to load audio: ' + err.message);
                                  }
                                }}
                              >
                                <Volume2 className="h-4 w-4 mr-1" /> Listen to Audio
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={async () => {
                                  try {
                                    const token = localStorage.getItem('auth_token');
                                    const url = `${getApiBaseUrl()}${step.data['📤 OUTPUT'].audio_download_url}`;
                                    const response = await fetch(url, {
                                      headers: { 'Authorization': `Bearer ${token}` }
                                    });
                                    if (!response.ok) throw new Error('Failed to download audio');
                                    const blob = await response.blob();
                                    const blobUrl = URL.createObjectURL(blob);
                                    const link = document.createElement('a');
                                    link.href = blobUrl;
                                    link.download = step.data['📤 OUTPUT'].audio_file_name || 'audio.webm';
                                    link.click();
                                    URL.revokeObjectURL(blobUrl);
                                  } catch (err: any) {
                                    alert('Failed to download audio: ' + err.message);
                                  }
                                }}
                              >
                                <Download className="h-4 w-4 mr-1" /> Download Audio
                              </Button>
                              <span className="text-xs text-[var(--text-low)]">
                                Available for {step.data['📤 OUTPUT'].audio_available_for || '30 minutes'}
                              </span>
                            </div>
                          )}
                        </>
                      )}

                      {step.error && (
                        <Alert variant="destructive">
                          <AlertDescription>
                            <span className="font-semibold text-xs">Error:</span>
                            <p className="text-sm">{step.error}</p>
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={stepsEndRef} />
              </div>
            </div>
          </div>
        )}

        {/* Final Result */}
        {finalResult && (
          <div className="surface-card p-5 border-t-4 border-t-green-500">
            <div className="flex items-center gap-3 mb-5">
              <CheckCircle2 className="h-8 w-8 text-green-400" />
              <div>
                <p className="text-xl font-semibold text-green-400">Transcription Complete</p>
                <p className="text-xs text-[var(--text-mid)]">All steps completed successfully</p>
              </div>
            </div>

            <div className="flex flex-col gap-6">
              {/* Statistics */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-4 text-center">
                  <span className="text-xs text-[var(--text-low)]">Confidence</span>
                  <p className="text-3xl font-bold text-green-400">{(finalResult.confidence * 100).toFixed(1)}%</p>
                </div>
                <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-4 text-center">
                  <span className="text-xs text-[var(--text-low)]">Duration</span>
                  <p className="text-3xl font-bold text-blue-400">{finalResult.duration_seconds}s</p>
                </div>
                <div className="rounded-lg border border-[var(--accent)]/20 bg-[var(--accent)]/5 p-4 text-center">
                  <span className="text-xs text-[var(--text-low)]">Text Length</span>
                  <p className="text-3xl font-bold text-[var(--accent)]">{finalResult.text?.length || 0}</p>
                  <span className="text-xs text-[var(--text-low)]">characters</span>
                </div>
              </div>

              <Separator />

              {/* Transcribed Text */}
              <div>
                <h4 className="font-semibold text-[var(--text-high)] mb-2">Transcribed Text (Raw):</h4>
                <div className="rounded-md border border-[var(--border)] bg-[var(--bg-elevated)] p-4 max-h-[300px] overflow-y-auto">
                  <p className="text-sm text-[var(--text-mid)] whitespace-pre-wrap">{finalResult.text}</p>
                </div>
              </div>

              <Separator />

              {/* AI Content Restructuring Section */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h4 className="text-lg font-semibold text-[var(--text-high)]">AI Content Restructuring</h4>
                  <Badge variant="success">FREE</Badge>
                </div>
                <p className="text-sm text-[var(--text-mid)] mb-4">
                  Transform the raw transcription into professional, engaging content. The AI will improve structure, clarity, and flow while preserving all original information. Maximum +50% enrichment.
                </p>

                <div className="flex gap-3 mb-6">
                  <Button
                    onClick={() => reformatWithAI('gemini')}
                    disabled={isReformattingGemini || isReformattingGroq}
                  >
                    {isReformattingGemini ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    {isReformattingGemini ? 'Restructuring...' : 'Restructure with Gemini'}
                  </Button>

                  <Button
                    variant="secondary"
                    onClick={() => reformatWithAI('groq')}
                    disabled={isReformattingGemini || isReformattingGroq}
                  >
                    {isReformattingGroq ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                    {isReformattingGroq ? 'Restructuring...' : 'Restructure with Groq'}
                  </Button>
                </div>

                {/* Gemini Result */}
                {geminiResult && (
                  <div className="mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <h5 className="font-semibold text-sm text-[var(--text-high)]">Gemini Result</h5>
                      <Badge variant="success">FREE</Badge>
                    </div>
                    <div className="rounded-md border border-[var(--border)] border-l-4 border-l-[var(--accent)] bg-[var(--bg-elevated)] p-4 max-h-[400px] overflow-y-auto">
                      <p className="text-sm text-[var(--text-mid)] whitespace-pre-wrap">{geminiResult}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-2"
                      onClick={() => {
                        navigator.clipboard.writeText(geminiResult);
                        alert('Gemini result copied to clipboard!');
                      }}
                    >
                      <Copy className="h-4 w-4 mr-1" /> Copy Gemini Result
                    </Button>
                  </div>
                )}

                {/* Groq Result */}
                {groqResult && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <h5 className="font-semibold text-sm text-[var(--text-high)]">Groq Result</h5>
                      <Badge variant="success">FREE</Badge>
                    </div>
                    <div className="rounded-md border border-[var(--border)] border-l-4 border-l-purple-500 bg-[var(--bg-elevated)] p-4 max-h-[400px] overflow-y-auto">
                      <p className="text-sm text-[var(--text-mid)] whitespace-pre-wrap">{groqResult}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-2"
                      onClick={() => {
                        navigator.clipboard.writeText(groqResult);
                        alert('Groq result copied to clipboard!');
                      }}
                    >
                      <Copy className="h-4 w-4 mr-1" /> Copy Groq Result
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Backend Test Result Modal */}
        <Dialog open={showBackendTestModal} onOpenChange={setShowBackendTestModal}>
          <DialogContent className="max-w-[70vw] max-h-[90vh] flex flex-col">
            <DialogHeader className={backendTestResult?.success ? 'bg-green-500/10 -mx-6 -mt-6 px-6 pt-6 pb-4 rounded-t-lg' : 'bg-red-500/10 -mx-6 -mt-6 px-6 pt-6 pb-4 rounded-t-lg'}>
              <div className="flex items-center gap-3">
                {backendTestResult?.success ? (
                  <CheckCircle2 className="h-8 w-8 text-green-400" />
                ) : (
                  <AlertCircle className="h-8 w-8 text-red-400" />
                )}
                <DialogTitle className="text-xl">Backend Test Result</DialogTitle>
              </div>
            </DialogHeader>

            <div className="overflow-y-auto flex-1 py-4">
              {backendTestResult && (
                <div className="flex flex-col gap-4">
                  {/* Status */}
                  <Alert variant={backendTestResult.success ? 'success' : 'destructive'}>
                    <AlertDescription>
                      <p className="font-semibold">
                        {backendTestResult.success ? 'Test Completed Successfully' : 'Test Failed'}
                      </p>
                      <p className="text-xs mt-1">
                        Exit Code: {backendTestResult.exit_code} | Timestamp: {new Date(backendTestResult.timestamp).toLocaleString()}
                      </p>
                    </AlertDescription>
                  </Alert>

                  {/* Output */}
                  <div>
                    <h4 className="font-semibold text-[var(--text-high)] mb-2">Test Output:</h4>
                    <div className="rounded-md border border-[var(--border)] bg-[var(--bg-elevated)] p-4 max-h-[500px] overflow-y-auto font-mono">
                      <pre className="whitespace-pre-wrap break-words text-sm text-[var(--text-mid)]">
                        {backendTestResult.output}
                      </pre>
                    </div>
                  </div>

                  {/* Error (if any) */}
                  {backendTestResult.error && (
                    <div>
                      <h4 className="font-semibold text-red-400 mb-2">Error Output:</h4>
                      <div className="rounded-md border border-red-500/30 bg-red-500/5 p-4 max-h-[300px] overflow-y-auto font-mono">
                        <pre className="whitespace-pre-wrap break-words text-sm text-red-400">
                          {backendTestResult.error}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(backendTestResult, null, 2));
                  alert('Test result copied to clipboard!');
                }}
              >
                <Copy className="h-4 w-4 mr-2" /> Copy Full Result
              </Button>
              <Button onClick={() => setShowBackendTestModal(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
