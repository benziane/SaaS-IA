'use client';

import { useRef, useState } from 'react';
import {
  Alert, Avatar, Box, Button, Card, CardContent, Chip, CircularProgress,
  Dialog, DialogActions, DialogContent, DialogTitle, Divider,
  FormControl, Grid, IconButton, InputLabel, MenuItem, Select,
  Skeleton, TextField, Typography,
} from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import MicIcon from '@mui/icons-material/Mic';
import StopIcon from '@mui/icons-material/Stop';
import SendIcon from '@mui/icons-material/Send';
import HistoryIcon from '@mui/icons-material/History';
import SummarizeIcon from '@mui/icons-material/Summarize';

import {
  useCreateSession, useEndSession, useRealtimeSessions, useSendMessage,
} from '@/features/realtime/hooks/useRealtime';
import type { RealtimeSession } from '@/features/realtime/types';

const MODE_ICONS: Record<string, string> = {
  voice: '🎤', vision: '👁️', voice_vision: '🎤👁️', meeting: '🏢',
};
const STATUS_COLORS: Record<string, 'success' | 'default' | 'error' | 'warning'> = {
  active: 'success', paused: 'warning', ended: 'default', failed: 'error',
};

export default function RealtimePage() {
  const { data: sessions, isLoading } = useRealtimeSessions();
  const createMutation = useCreateSession();
  const endMutation = useEndSession();

  const [activeSession, setActiveSession] = useState<RealtimeSession | null>(null);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [mode, setMode] = useState('voice');
  const [provider, setProvider] = useState('gemini');
  const [systemPrompt, setSystemPrompt] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  const sendMutation = useSendMessage(activeSession?.id || '');

  const handleCreate = () => {
    createMutation.mutate(
      { title: `Session ${new Date().toLocaleTimeString()}`, mode, provider, system_prompt: systemPrompt || undefined },
      { onSuccess: (s) => { setActiveSession(s); setChatHistory([]); } },
    );
  };

  const handleSend = () => {
    if (!message.trim() || !activeSession) return;
    const userMsg = message;
    setChatHistory((prev) => [...prev, { role: 'user', content: userMsg }]);
    setMessage('');
    sendMutation.mutate(userMsg, {
      onSuccess: (result) => {
        const aiMsg = (result as Record<string, Record<string, string>>).ai_message;
        if (aiMsg) setChatHistory((prev) => [...prev, { role: 'assistant', content: aiMsg.content }]);
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      },
    });
  };

  const handleEnd = () => {
    if (!activeSession) return;
    endMutation.mutate(activeSession.id, {
      onSuccess: () => { setActiveSession(null); setChatHistory([]); },
    });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SmartToyIcon color="primary" /> Realtime AI
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Live AI conversations with voice, vision, and knowledge base integration
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Chat Area */}
        <Grid item xs={12} md={8}>
          {activeSession ? (
            <Card sx={{ height: '70vh', display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: 1, borderColor: 'divider' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip label={MODE_ICONS[activeSession.mode] || '🎤'} size="small" />
                  <Typography variant="subtitle1">{activeSession.title}</Typography>
                  <Chip label="LIVE" color="success" size="small" />
                </Box>
                <Button color="error" variant="outlined" size="small" startIcon={<StopIcon />} onClick={handleEnd}>
                  End Session
                </Button>
              </Box>

              {/* Messages */}
              <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
                {chatHistory.map((msg, i) => (
                  <Box key={i} sx={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', mb: 1.5 }}>
                    <Box sx={{
                      maxWidth: '75%', p: 1.5, borderRadius: 2,
                      bgcolor: msg.role === 'user' ? 'primary.main' : 'action.hover',
                      color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
                    }}>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{msg.content}</Typography>
                    </Box>
                  </Box>
                ))}
                {sendMutation.isPending && (
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', color: 'text.secondary' }}>
                    <CircularProgress size={16} /> <Typography variant="caption">AI is thinking...</Typography>
                  </Box>
                )}
                <div ref={chatEndRef} />
              </Box>

              {/* Input */}
              <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', display: 'flex', gap: 1 }}>
                <TextField fullWidth size="small" placeholder="Type a message..."
                  value={message} onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }} />
                <IconButton color="primary" onClick={handleSend} disabled={!message.trim() || sendMutation.isPending}>
                  <SendIcon />
                </IconButton>
              </Box>
            </Card>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <SmartToyIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" sx={{ mb: 2 }}>Start a Realtime AI Session</Typography>
                <Grid container spacing={2} justifyContent="center" sx={{ mb: 3, maxWidth: 500, mx: 'auto' }}>
                  <Grid item xs={6}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Mode</InputLabel>
                      <Select value={mode} label="Mode" onChange={(e) => setMode(e.target.value)}>
                        <MenuItem value="voice">Voice Chat</MenuItem>
                        <MenuItem value="vision">Vision Analysis</MenuItem>
                        <MenuItem value="voice_vision">Voice + Vision</MenuItem>
                        <MenuItem value="meeting">Meeting Assistant</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={6}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Provider</InputLabel>
                      <Select value={provider} label="Provider" onChange={(e) => setProvider(e.target.value)}>
                        <MenuItem value="gemini">Gemini Flash</MenuItem>
                        <MenuItem value="groq">Groq (Ultra-fast)</MenuItem>
                        <MenuItem value="claude">Claude</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12}>
                    <TextField fullWidth size="small" label="System Prompt (optional)"
                      placeholder="e.g., You are a helpful coding assistant..."
                      value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} />
                  </Grid>
                </Grid>
                <Button variant="contained" size="large" startIcon={
                  createMutation.isPending ? <CircularProgress size={18} color="inherit" /> : <MicIcon />
                } onClick={handleCreate} disabled={createMutation.isPending}>
                  Start Session
                </Button>
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Session History */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <HistoryIcon /> Sessions
              </Typography>
              {isLoading ? <Skeleton variant="rectangular" height={300} /> : !sessions?.length ? (
                <Typography color="text.secondary">No sessions yet</Typography>
              ) : (
                sessions.map((s) => (
                  <Card key={s.id} variant="outlined" sx={{ mb: 1 }}>
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="subtitle2">{s.title || 'Untitled'}</Typography>
                        <Chip label={s.status} size="small" color={STATUS_COLORS[s.status] || 'default'} />
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                        <Chip label={MODE_ICONS[s.mode] || s.mode} size="small" variant="outlined" />
                        <Chip label={s.provider} size="small" variant="outlined" />
                        <Chip label={`${s.total_turns} turns`} size="small" variant="outlined" />
                      </Box>
                    </CardContent>
                  </Card>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
