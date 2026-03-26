'use client';

import { useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  Grid, Skeleton,
  Slider, TextField, Typography,
} from '@mui/material';
import VideocamIcon from '@mui/icons-material/Videocam';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import DeleteIcon from '@mui/icons-material/Delete';
import IconButton from '@mui/material/IconButton';
import MovieFilterIcon from '@mui/icons-material/MovieFilter';
import PersonIcon from '@mui/icons-material/Person';

import { useDeleteVideo, useGenerateAvatar, useGenerateVideo, useVideos } from '@/features/video-gen/hooks/useVideoGen';

const VIDEO_TYPES = [
  { id: 'text_to_video', label: 'Text to Video', icon: '🎬' },
  { id: 'explainer', label: 'Explainer', icon: '📖' },
  { id: 'short_form', label: 'Short Form', icon: '📱' },
  { id: 'avatar_talking', label: 'Talking Avatar', icon: '🧑' },
];

const STATUS_COLORS: Record<string, 'default' | 'info' | 'success' | 'error'> = {
  pending: 'default', generating: 'info', processing: 'info', completed: 'success', failed: 'error',
};

export default function VideoStudioPage() {
  const { data: videos, isLoading } = useVideos();
  const genMutation = useGenerateVideo();
  const avatarMutation = useGenerateAvatar();
  const deleteMutation = useDeleteVideo();

  const [title, setTitle] = useState('');
  const [prompt, setPrompt] = useState('');
  const [videoType, setVideoType] = useState('text_to_video');
  const [duration, setDuration] = useState(10);
  const [avatarText, setAvatarText] = useState('');

  const handleGenerate = () => {
    if (!title.trim() || !prompt.trim()) return;
    genMutation.mutate({ title, prompt, video_type: videoType, duration_s: duration });
  };

  const handleAvatar = () => {
    if (!avatarText.trim()) return;
    avatarMutation.mutate({ text: avatarText });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <VideocamIcon color="primary" /> Video Studio
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Generate AI videos, highlight clips, talking avatars, and explainer videos
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Generation */}
        <Grid item xs={12} md={5}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <MovieFilterIcon /> Generate Video
              </Typography>
              <TextField fullWidth size="small" label="Title" value={title}
                onChange={(e) => setTitle(e.target.value)} sx={{ mb: 2 }} />
              <TextField fullWidth multiline rows={3} label="Prompt" placeholder="Describe the video you want to create..."
                value={prompt} onChange={(e) => setPrompt(e.target.value)} sx={{ mb: 2 }} />

              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                {VIDEO_TYPES.filter((t) => t.id !== 'avatar_talking').map((t) => (
                  <Chip key={t.id} label={`${t.icon} ${t.label}`} size="small"
                    variant={videoType === t.id ? 'filled' : 'outlined'}
                    color={videoType === t.id ? 'primary' : 'default'}
                    onClick={() => setVideoType(t.id)} />
                ))}
              </Box>

              <Typography variant="caption" color="text.secondary">Duration: {duration}s</Typography>
              <Slider value={duration} onChange={(_, v) => setDuration(v as number)}
                min={5} max={120} step={5} valueLabelDisplay="auto" sx={{ mb: 2 }} />

              <Button variant="contained" fullWidth onClick={handleGenerate}
                disabled={!title.trim() || !prompt.trim() || genMutation.isPending}
                startIcon={genMutation.isPending ? <CircularProgress size={18} color="inherit" /> : <AutoAwesomeIcon />}>
                {genMutation.isPending ? 'Generating...' : 'Generate Video'}
              </Button>
              {genMutation.isError && <Alert severity="error" sx={{ mt: 1 }}>{genMutation.error.message}</Alert>}
            </CardContent>
          </Card>

          {/* Avatar */}
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon /> Talking Avatar
              </Typography>
              <TextField fullWidth multiline rows={3} label="Script" placeholder="What should the avatar say?"
                value={avatarText} onChange={(e) => setAvatarText(e.target.value)} sx={{ mb: 2 }} />
              <Button variant="outlined" fullWidth onClick={handleAvatar}
                disabled={!avatarText.trim() || avatarMutation.isPending}
                startIcon={avatarMutation.isPending ? <CircularProgress size={18} /> : <PersonIcon />}>
                Generate Avatar Video
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Gallery */}
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Videos</Typography>
              {isLoading ? <Skeleton variant="rectangular" height={400} /> : !videos?.length ? (
                <Box sx={{ textAlign: 'center', py: 6 }}>
                  <VideocamIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 1 }} />
                  <Typography color="text.secondary">No videos yet</Typography>
                </Box>
              ) : (
                <Grid container spacing={1.5}>
                  {videos.map((v) => (
                    <Grid item xs={12} sm={6} key={v.id}>
                      <Card variant="outlined">
                        <Box sx={{ height: 120, bgcolor: 'action.hover', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          {v.status === 'completed' ? (
                            <Typography variant="caption" sx={{ p: 1 }}>{v.title}</Typography>
                          ) : v.status === 'failed' ? (
                            <Typography color="error" variant="caption">Failed</Typography>
                          ) : (
                            <CircularProgress size={24} />
                          )}
                        </Box>
                        <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
                          <Typography variant="subtitle2" noWrap>{v.title}</Typography>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 0.5 }}>
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                              <Chip label={v.video_type.replace('_', ' ')} size="small" variant="outlined" />
                              <Chip label={v.status} size="small" color={STATUS_COLORS[v.status] || 'default'} />
                              {v.duration_s && <Chip label={`${v.duration_s}s`} size="small" variant="outlined" />}
                            </Box>
                            <IconButton size="small" color="error" onClick={() => deleteMutation.mutate(v.id)}>
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
