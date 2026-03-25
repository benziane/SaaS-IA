'use client';

import { useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  Dialog, DialogActions, DialogContent, DialogTitle, Divider,
  FormControl, Grid, InputLabel, MenuItem, Select, Skeleton,
  Slider, TextField, Typography,
} from '@mui/material';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import TranslateIcon from '@mui/icons-material/Translate';

import { useBuiltinVoices, useSynthesize, useSyntheses } from '@/features/voice/hooks/useVoice';

const STATUS_COLORS: Record<string, 'default' | 'success' | 'error' | 'info'> = {
  pending: 'default', processing: 'info', completed: 'success', failed: 'error',
};

export default function VoicePage() {
  const { data: voices } = useBuiltinVoices();
  const { data: syntheses, isLoading } = useSyntheses();
  const synthesizeMutation = useSynthesize();

  const [text, setText] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('alloy');
  const [provider, setProvider] = useState('openai');
  const [speed, setSpeed] = useState(1.0);
  const [language, setLanguage] = useState('auto');

  const handleSynthesize = () => {
    if (!text.trim()) return;
    synthesizeMutation.mutate({
      text, voice_id: selectedVoice, provider, language, speed,
    });
  };

  const filteredVoices = voices?.filter((v) => v.provider === provider) || [];

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <RecordVoiceOverIcon color="primary" /> Voice Studio
        </Typography>
        <Typography variant="body2" color="text.secondary">
          AI voice cloning, text-to-speech, and automatic dubbing
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* TTS Input */}
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Text to Speech</Typography>
              <TextField fullWidth multiline rows={6} label="Text to speak"
                placeholder="Enter the text you want to convert to speech..."
                value={text} onChange={(e) => setText(e.target.value)} sx={{ mb: 2 }} />

              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Provider</InputLabel>
                    <Select value={provider} label="Provider" onChange={(e) => setProvider(e.target.value)}>
                      <MenuItem value="openai">OpenAI TTS</MenuItem>
                      <MenuItem value="elevenlabs">ElevenLabs</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={4}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Voice</InputLabel>
                    <Select value={selectedVoice} label="Voice" onChange={(e) => setSelectedVoice(e.target.value)}>
                      {filteredVoices.map((v) => (
                        <MenuItem key={v.id} value={v.id}>{v.name} ({v.gender})</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={4}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Language</InputLabel>
                    <Select value={language} label="Language" onChange={(e) => setLanguage(e.target.value)}>
                      <MenuItem value="auto">Auto</MenuItem>
                      <MenuItem value="en">English</MenuItem>
                      <MenuItem value="fr">French</MenuItem>
                      <MenuItem value="es">Spanish</MenuItem>
                      <MenuItem value="de">German</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>

              <Box sx={{ mt: 2, px: 1 }}>
                <Typography variant="caption" color="text.secondary">Speed: {speed}x</Typography>
                <Slider value={speed} onChange={(_, v) => setSpeed(v as number)}
                  min={0.5} max={2.0} step={0.1} valueLabelDisplay="auto" />
              </Box>

              <Button variant="contained" fullWidth startIcon={
                synthesizeMutation.isPending ? <CircularProgress size={18} color="inherit" /> : <VolumeUpIcon />
              } onClick={handleSynthesize} disabled={!text.trim() || synthesizeMutation.isPending}
                sx={{ mt: 2 }}>
                {synthesizeMutation.isPending ? 'Generating...' : 'Generate Speech'}
              </Button>

              {synthesizeMutation.isError && (
                <Alert severity="error" sx={{ mt: 2 }}>{synthesizeMutation.error.message}</Alert>
              )}
              {synthesizeMutation.isSuccess && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  Audio generated! Status: {synthesizeMutation.data.status}
                  {synthesizeMutation.data.audio_url && (
                    <Box sx={{ mt: 1 }}>
                      <Chip label={`Duration: ~${synthesizeMutation.data.duration_s?.toFixed(1)}s`} size="small" />
                    </Box>
                  )}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* History */}
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Synthesis History</Typography>
              {isLoading ? <Skeleton variant="rectangular" height={300} /> : !syntheses?.length ? (
                <Typography color="text.secondary">No syntheses yet</Typography>
              ) : (
                syntheses.map((s) => (
                  <Card key={s.id} variant="outlined" sx={{ mb: 1 }}>
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Chip label={s.status} size="small" color={STATUS_COLORS[s.status] || 'default'} sx={{ mr: 0.5 }} />
                          <Chip label={s.provider} size="small" variant="outlined" sx={{ mr: 0.5 }} />
                          {s.target_language && <Chip icon={<TranslateIcon />} label={s.target_language} size="small" variant="outlined" />}
                        </Box>
                        {s.duration_s && <Typography variant="caption">{s.duration_s.toFixed(1)}s</Typography>}
                      </Box>
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                        {new Date(s.created_at).toLocaleString()}
                      </Typography>
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
