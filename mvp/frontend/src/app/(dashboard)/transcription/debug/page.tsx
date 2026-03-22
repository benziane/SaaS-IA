'use client';

/**
 * Transcription Debug Page - Grade S++
 * Real-time debugging interface for YouTube transcription
 * Uses Sneat template design system with Material-UI
 */

import { useState, useEffect, useRef } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  TextField,
  Button,
  Box,
  Chip,
  Alert,
  CircularProgress,
  Paper,
  Divider,
  LinearProgress,
  Stack,
  IconButton,
  Tooltip,
  useTheme,
  Modal,
  Backdrop,
  Fade,
} from '@mui/material';
import {
  PlayArrow,
  CheckCircle,
  Error as ErrorIcon,
  AccessTime,
  BugReport,
  Download,
  VolumeUp,
  ContentCopy,
  Refresh,
  Science,
  Close,
} from '@mui/icons-material';
import apiClient, { extractErrorMessage } from '@/lib/apiClient';

/* ========================================================================
   URL UTILITIES
   ======================================================================== */

/**
 * Returns the base API URL from environment or fallback.
 */
function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004';
}

/**
 * Derives a WebSocket URL from the HTTP API base URL.
 * Replaces http:// with ws:// and https:// with wss://.
 */
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
   UTILITIES
   ======================================================================== */

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function TranscriptionDebugPage() {
  // Theme
  const theme = useTheme();
  
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

  // Auto-scroll to bottom when new steps arrive
  useEffect(() => {
    stepsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [debugSteps]);

  // Cleanup WebSocket on unmount
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
          // Check if a step with the same name already exists
          const existingIndex = prev.findIndex(s => s.step === message.step.step);
          
          if (existingIndex !== -1) {
            // Update existing step
            const updated = [...prev];
            updated[existingIndex] = message.step;
            return updated;
          } else {
            // Add new step
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

    // Send ping every 30 seconds to keep connection alive
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
      // Generate a unique job ID for this transcription
      const tempJobId = `debug-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      setJobId(tempJobId);
      
      // STEP 1: Connect WebSocket FIRST (before starting transcription)
      console.log('[Debug] Connecting WebSocket first...');
      connectWebSocket(tempJobId);
      
      // Wait for WebSocket to be ready
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      // STEP 2: Start transcription (synchronous endpoint that waits for completion)
      console.log('[Debug] Starting transcription with job_id:', tempJobId);
      const response = await apiClient.post(`/api/transcription/debug/transcribe/${tempJobId}`, {
        video_url: videoUrl
      }, {
        timeout: 300000 // 5 minutes for transcription (YouTube download + AssemblyAI + AI Router)
      });

      const result = response.data;
      console.log('[Debug] Transcription complete:', result);
      
      // Update with final result
      setFinalResult(result);
      setIsProcessing(false);
      
      // Close WebSocket
      if (wsRef.current) {
        wsRef.current.close();
      }
      
    } catch (err: any) {
      console.error('[Debug] Error:', err);
      setError(err.message || 'An error occurred');
      setIsProcessing(false);
      
      // Close WebSocket on error
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
    alert('✅ All logs copied to clipboard! You can now paste them to share.');
  };

  /* ========================================================================
     RENDER HELPERS
     ======================================================================== */

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'ERROR':
      case 'FAILED':
        return <ErrorIcon sx={{ color: 'error.main' }} />;
      case 'IN_PROGRESS':
        return <CircularProgress size={20} />;
      default:
        return <AccessTime sx={{ color: 'text.secondary' }} />;
    }
  };

  const getStatusColor = (status: string): 'success' | 'error' | 'info' | 'default' => {
    switch (status) {
      case 'SUCCESS':
        return 'success';
      case 'ERROR':
      case 'FAILED':
        return 'error';
      case 'IN_PROGRESS':
        return 'info';
      default:
        return 'default';
    }
  };

  /* ========================================================================
     RENDER
     ======================================================================== */

  return (
    <Box sx={{ p: 3 }}>
      {/* Header Card */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          avatar={<BugReport sx={{ fontSize: 32, color: 'primary.main' }} />}
          title={
            <Typography variant="h4" component="h1">
              Transcription Debug
            </Typography>
          }
          subheader="Real-time debugging interface for YouTube transcription"
          action={
            debugSteps.length > 0 && (
              <Tooltip title="Reset">
                <IconButton onClick={handleReset} color="primary">
                  <Refresh />
                </IconButton>
              </Tooltip>
            )
          }
        />
        <CardContent>
          <Stack spacing={2}>
            <TextField
              fullWidth
              label="YouTube URL"
              placeholder="https://youtu.be/..."
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              disabled={isProcessing}
              variant="outlined"
              helperText="Enter a YouTube video URL to start debugging"
            />
            
            <Button
              variant="contained"
              size="large"
              onClick={startTranscription}
              disabled={isProcessing || !videoUrl.trim()}
              startIcon={isProcessing ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
              fullWidth
            >
              {isProcessing ? 'Processing...' : 'Start Debug Transcription'}
            </Button>

            <Divider sx={{ my: 2 }}>
              <Chip label="OR" size="small" />
            </Divider>

            <Button
              variant="outlined"
              size="large"
              color="secondary"
              onClick={runBackendTest}
              disabled={isBackendTestRunning || isProcessing}
              startIcon={isBackendTestRunning ? <CircularProgress size={20} color="inherit" /> : <Science />}
              fullWidth
            >
              {isBackendTestRunning ? 'Running Backend Test...' : '🧪 Run Full Backend Test (Python)'}
            </Button>

            <Alert severity="info" icon={<Science />}>
              <Typography variant="body2">
                <strong>Backend Test:</strong> Runs the complete transcription pipeline in Python (backend-only).
                This test uses the default video and displays the final result with AI improvements.
              </Typography>
            </Alert>

            {jobId && (
              <Alert 
                severity="info" 
                action={
                  <Tooltip title="Copy Job ID">
                    <IconButton size="small" onClick={copyJobId}>
                      <ContentCopy fontSize="small" />
                    </IconButton>
                  </Tooltip>
                }
              >
                <strong>Job ID:</strong> {jobId}
              </Alert>
            )}

            {error && (
              <Alert severity="error" onClose={() => setError(null)}>
                {error}
              </Alert>
            )}
          </Stack>
        </CardContent>
        
        {isProcessing && <LinearProgress />}
      </Card>

      {/* Debug Logs Export */}
      {debugSteps.length > 0 && (
        <Card sx={{ mb: 3, bgcolor: 'info.lighter' }}>
          <CardHeader
            avatar={<ContentCopy sx={{ color: 'info.main' }} />}
            title="Export Debug Logs"
            subheader="Copy all logs to share for debugging"
            action={
              <Button
                variant="contained"
                color="info"
                startIcon={<ContentCopy />}
                onClick={copyAllLogs}
              >
                Copy All Logs
              </Button>
            }
          />
          <CardContent>
            <Alert severity="info">
              Click "Copy All Logs" to copy all transcription data (steps, errors, results) to your clipboard in JSON format. 
              You can then paste it to share for debugging.
            </Alert>
          </CardContent>
        </Card>
      )}

      {/* Debug Steps */}
      {debugSteps.length > 0 && (
        <Card>
          <CardHeader 
            title={`Debug Steps (${debugSteps.length})`}
            subheader="Real-time transcription process"
          />
          <CardContent>
            <Box sx={{ maxHeight: 600, overflowY: 'auto' }}>
              <Stack spacing={2}>
                {debugSteps.map((step, index) => (
                  <Paper
                    key={index}
                    elevation={2}
                    sx={{
                      p: 2,
                      borderLeft: 4,
                      borderColor: step.status === 'SUCCESS' ? 'success.main' : 
                                  step.status === 'ERROR' || step.status === 'FAILED' ? 'error.main' :
                                  step.status === 'IN_PROGRESS' ? 'info.main' : 'grey.300',
                      bgcolor: theme.palette.mode === 'dark' ? 'background.default' : 'background.paper',
                    }}
                  >
                    <Stack spacing={1}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getStatusIcon(step.status)}
                          <Typography variant="subtitle1" fontWeight="bold">
                            {step.step}
                          </Typography>
                          <Chip
                            label={step.status}
                            color={getStatusColor(step.status)}
                            size="small"
                          />
                        </Box>
                        <Chip
                          label={`${step.duration_seconds.toFixed(2)}s`}
                          variant="outlined"
                          size="small"
                        />
                      </Box>

                      {step.data && Object.keys(step.data).length > 0 && (
                        <>
                          <Paper 
                            variant="outlined" 
                            sx={{ 
                              p: 2, 
                              bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
                              maxHeight: 300,
                              overflowY: 'auto'
                            }}
                          >
                            <Typography variant="caption" fontWeight="bold" color="text.secondary">
                              Data:
                            </Typography>
                            <pre style={{ 
                              fontSize: '0.75rem', 
                              overflow: 'auto', 
                              margin: '8px 0 0 0',
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word'
                            }}>
                              {JSON.stringify(step.data, null, 2)}
                            </pre>
                          </Paper>
                          
                          {/* Audio download buttons for step 2 */}
                          {step.step.includes('AUDIO DOWNLOAD') && 
                           step.status === 'SUCCESS' && 
                           step.data['📤 OUTPUT']?.audio_download_url && (
                            <Stack direction="row" spacing={1}>
                              <Button
                                variant="contained"
                                color="primary"
                                size="small"
                                startIcon={<VolumeUp />}
                                onClick={async () => {
                                  try {
                                    const token = localStorage.getItem('auth_token');
                                    const url = `${getApiBaseUrl()}${step.data['📤 OUTPUT'].audio_download_url}`;

                                    const response = await fetch(url, {
                                      headers: {
                                        'Authorization': `Bearer ${token}`
                                      }
                                    });

                                    if (!response.ok) {
                                      throw new Error('Failed to load audio');
                                    }
                                    
                                    const blob = await response.blob();
                                    const blobUrl = URL.createObjectURL(blob);
                                    window.open(blobUrl, '_blank');
                                  } catch (err: any) {
                                    alert('Failed to load audio: ' + err.message);
                                  }
                                }}
                              >
                                🎧 Listen to Audio
                              </Button>
                              <Button
                                variant="outlined"
                                size="small"
                                startIcon={<Download />}
                                onClick={async () => {
                                  try {
                                    const token = localStorage.getItem('auth_token');
                                    const url = `${getApiBaseUrl()}${step.data['📤 OUTPUT'].audio_download_url}`;

                                    const response = await fetch(url, {
                                      headers: {
                                        'Authorization': `Bearer ${token}`
                                      }
                                    });

                                    if (!response.ok) {
                                      throw new Error('Failed to download audio');
                                    }
                                    
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
                                Download Audio
                              </Button>
                              <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
                                ⏰ Available for {step.data['📤 OUTPUT'].audio_available_for || '30 minutes'}
                              </Typography>
                            </Stack>
                          )}
                        </>
                      )}

                      {step.error && (
                        <Alert severity="error">
                          <Typography variant="caption" fontWeight="bold">
                            Error:
                          </Typography>
                          <Typography variant="body2">{step.error}</Typography>
                        </Alert>
                      )}
                    </Stack>
                  </Paper>
                ))}
                <div ref={stepsEndRef} />
              </Stack>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Final Result */}
      {finalResult && (
        <Card sx={{ mt: 3, borderTop: 4, borderColor: 'success.main' }}>
          <CardHeader
            avatar={<CheckCircle sx={{ fontSize: 32, color: 'success.main' }} />}
            title={
              <Typography variant="h5" color="success.main">
                Transcription Complete
              </Typography>
            }
            subheader="All steps completed successfully"
          />
          <CardContent>
            <Stack spacing={3}>
              {/* Statistics */}
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 3 }}>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.lighter' }}>
                  <Typography variant="caption" color="text.secondary">
                    Confidence
                  </Typography>
                  <Typography variant="h3" fontWeight="bold" color="success.main">
                    {(finalResult.confidence * 100).toFixed(1)}%
                  </Typography>
                </Paper>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.lighter' }}>
                  <Typography variant="caption" color="text.secondary">
                    Duration
                  </Typography>
                  <Typography variant="h3" fontWeight="bold" color="info.main">
                    {finalResult.duration_seconds}s
                  </Typography>
                </Paper>
                <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.lighter' }}>
                  <Typography variant="caption" color="text.secondary">
                    Text Length
                  </Typography>
                  <Typography variant="h3" fontWeight="bold" color="primary.main">
                    {finalResult.text?.length || 0}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    characters
                  </Typography>
                </Paper>
              </Box>

              <Divider />

              {/* Transcribed Text */}
              <Box>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Transcribed Text (Raw):
                </Typography>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    maxHeight: 300,
                    overflowY: 'auto',
                    bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
                  }}
                >
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                    {finalResult.text}
                  </Typography>
                </Paper>
              </Box>

              <Divider />

              {/* AI Content Restructuring Section */}
              <Box>
                <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  🤖 AI Content Restructuring
                  <Chip label="FREE" color="success" size="small" />
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Transform the raw transcription into professional, engaging content. The AI will improve structure, clarity, and flow while preserving all original information. Maximum +50% enrichment.
                </Typography>
                
                <Stack direction="row" spacing={2} sx={{ mt: 2, mb: 3 }}>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => reformatWithAI('gemini')}
                    disabled={isReformattingGemini || isReformattingGroq}
                    startIcon={isReformattingGemini ? <CircularProgress size={20} color="inherit" /> : null}
                  >
                    {isReformattingGemini ? 'Restructuring...' : '✨ Restructure with Gemini'}
                  </Button>
                  
                  <Button
                    variant="contained"
                    color="secondary"
                    onClick={() => reformatWithAI('groq')}
                    disabled={isReformattingGemini || isReformattingGroq}
                    startIcon={isReformattingGroq ? <CircularProgress size={20} color="inherit" /> : null}
                  >
                    {isReformattingGroq ? 'Restructuring...' : '⚡ Restructure with Groq'}
                  </Button>
                </Stack>

                {/* Gemini Result */}
                {geminiResult && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      ✨ Gemini Result
                      <Chip label="FREE 🆓" color="success" size="small" />
                    </Typography>
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 2,
                        maxHeight: 400,
                        overflowY: 'auto',
                        bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
                        borderLeft: 4,
                        borderColor: 'primary.main',
                      }}
                    >
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {geminiResult}
                      </Typography>
                    </Paper>
                    <Button
                      size="small"
                      startIcon={<ContentCopy />}
                      onClick={() => {
                        navigator.clipboard.writeText(geminiResult);
                        alert('Gemini result copied to clipboard!');
                      }}
                      sx={{ mt: 1 }}
                    >
                      Copy Gemini Result
                    </Button>
                  </Box>
                )}

                {/* Groq Result */}
                {groqResult && (
                  <Box>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      ⚡ Groq Result
                      <Chip label="FREE 🆓" color="success" size="small" />
                    </Typography>
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 2,
                        maxHeight: 400,
                        overflowY: 'auto',
                        bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
                        borderLeft: 4,
                        borderColor: 'secondary.main',
                      }}
                    >
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {groqResult}
                      </Typography>
                    </Paper>
                    <Button
                      size="small"
                      startIcon={<ContentCopy />}
                      onClick={() => {
                        navigator.clipboard.writeText(groqResult);
                        alert('Groq result copied to clipboard!');
                      }}
                      sx={{ mt: 1 }}
                    >
                      Copy Groq Result
                    </Button>
                  </Box>
                )}
              </Box>
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* Backend Test Result Modal */}
      <Modal
        open={showBackendTestModal}
        onClose={() => setShowBackendTestModal(false)}
        closeAfterTransition
        BackdropComponent={Backdrop}
        BackdropProps={{
          timeout: 500,
        }}
      >
        <Fade in={showBackendTestModal}>
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: { xs: '90%', sm: '80%', md: '70%', lg: '60%' },
              maxHeight: '90vh',
              bgcolor: 'background.paper',
              boxShadow: 24,
              borderRadius: 2,
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Modal Header */}
            <Box
              sx={{
                p: 2,
                borderBottom: 1,
                borderColor: 'divider',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                bgcolor: backendTestResult?.success ? 'success.lighter' : 'error.lighter',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {backendTestResult?.success ? (
                  <CheckCircle sx={{ color: 'success.main', fontSize: 32 }} />
                ) : (
                  <ErrorIcon sx={{ color: 'error.main', fontSize: 32 }} />
                )}
                <Typography variant="h5" fontWeight="bold">
                  Backend Test Result
                </Typography>
              </Box>
              <IconButton onClick={() => setShowBackendTestModal(false)}>
                <Close />
              </IconButton>
            </Box>

            {/* Modal Content */}
            <Box sx={{ p: 3, overflowY: 'auto', flex: 1 }}>
              {backendTestResult && (
                <Stack spacing={3}>
                  {/* Status */}
                  <Alert severity={backendTestResult.success ? 'success' : 'error'}>
                    <Typography variant="body1" fontWeight="bold">
                      {backendTestResult.success ? '✅ Test Completed Successfully' : '❌ Test Failed'}
                    </Typography>
                    <Typography variant="caption">
                      Exit Code: {backendTestResult.exit_code} | Timestamp: {new Date(backendTestResult.timestamp).toLocaleString()}
                    </Typography>
                  </Alert>

                  {/* Output */}
                  <Box>
                    <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                      Test Output:
                    </Typography>
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 2,
                        maxHeight: 500,
                        overflowY: 'auto',
                        bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
                        fontFamily: 'monospace',
                      }}
                    >
                      <pre style={{ 
                        margin: 0, 
                        whiteSpace: 'pre-wrap', 
                        wordBreak: 'break-word',
                        fontSize: '0.875rem'
                      }}>
                        {backendTestResult.output}
                      </pre>
                    </Paper>
                  </Box>

                  {/* Error (if any) */}
                  {backendTestResult.error && (
                    <Box>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom color="error">
                        Error Output:
                      </Typography>
                      <Paper
                        variant="outlined"
                        sx={{
                          p: 2,
                          maxHeight: 300,
                          overflowY: 'auto',
                          bgcolor: 'error.lighter',
                          fontFamily: 'monospace',
                        }}
                      >
                        <pre style={{ 
                          margin: 0, 
                          whiteSpace: 'pre-wrap', 
                          wordBreak: 'break-word',
                          fontSize: '0.875rem',
                          color: theme.palette.error.main
                        }}>
                          {backendTestResult.error}
                        </pre>
                      </Paper>
                    </Box>
                  )}

                  {/* Actions */}
                  <Stack direction="row" spacing={2} justifyContent="flex-end">
                    <Button
                      variant="outlined"
                      startIcon={<ContentCopy />}
                      onClick={() => {
                        navigator.clipboard.writeText(JSON.stringify(backendTestResult, null, 2));
                        alert('Test result copied to clipboard!');
                      }}
                    >
                      Copy Full Result
                    </Button>
                    <Button
                      variant="contained"
                      onClick={() => setShowBackendTestModal(false)}
                    >
                      Close
                    </Button>
                  </Stack>
                </Stack>
              )}
            </Box>
          </Box>
        </Fade>
      </Modal>
    </Box>
  );
}
