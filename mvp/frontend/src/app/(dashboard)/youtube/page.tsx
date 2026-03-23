'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';

import { autoChapter, getMetadata, smartTranscribe, transcribePlaylist } from '@/features/transcription/api';
import type { AutoChapterResponse, PlaylistTranscribeResponse, SmartTranscribeResponse, YouTubeMetadata } from '@/features/transcription/types';

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function formatNumber(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return String(n);
}

function ProviderChip({ provider }: { provider: string }) {
  const colors: Record<string, 'success' | 'primary' | 'warning' | 'default'> = {
    youtube_subtitles: 'success',
    whisper: 'primary',
    assemblyai: 'warning',
  };
  const labels: Record<string, string> = {
    youtube_subtitles: 'YouTube Subs (Free)',
    whisper: 'Whisper (Local)',
    assemblyai: 'AssemblyAI (Paid)',
  };
  return <Chip label={labels[provider] || provider} size="small" color={colors[provider] || 'default'} />;
}

function MetadataCard({ data }: { data: YouTubeMetadata }) {
  return (
    <Card>
      <Grid container>
        {data.thumbnail && (
          <Grid item xs={12} md={4}>
            <CardMedia component="img" image={data.thumbnail} alt={data.title} sx={{ height: '100%', minHeight: 200, objectFit: 'cover' }} />
          </Grid>
        )}
        <Grid item xs={12} md={data.thumbnail ? 8 : 12}>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>{data.title}</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              <Chip label={data.uploader} size="small" variant="outlined" />
              <Chip label={formatDuration(data.duration_seconds)} size="small" />
              <Chip label={`${formatNumber(data.view_count)} views`} size="small" />
              <Chip label={`${formatNumber(data.like_count)} likes`} size="small" />
              {data.is_live && <Chip label="LIVE" size="small" color="error" />}
            </Box>
            {data.description && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxHeight: 100, overflow: 'auto', whiteSpace: 'pre-wrap' }}>
                {data.description.substring(0, 500)}{data.description.length > 500 ? '...' : ''}
              </Typography>
            )}
            {data.tags.length > 0 && (
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
                {data.tags.slice(0, 10).map((tag) => (
                  <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ fontSize: '0.7rem' }} />
                ))}
              </Box>
            )}
            {data.chapters.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="subtitle2" sx={{ mb: 0.5 }}>{data.chapters.length} Chapters</Typography>
                {data.chapters.slice(0, 5).map((ch, i) => (
                  <Typography key={i} variant="caption" display="block" color="text.secondary">
                    {formatDuration(Math.round(ch.start_time))} - {ch.title}
                  </Typography>
                ))}
                {data.chapters.length > 5 && (
                  <Typography variant="caption" color="text.secondary">+{data.chapters.length - 5} more</Typography>
                )}
              </Box>
            )}
          </CardContent>
        </Grid>
      </Grid>
    </Card>
  );
}

export default function YouTubePage() {
  const [url, setUrl] = useState('');
  const [tab, setTab] = useState(0);
  const [language, setLanguage] = useState('auto');

  const smartMutation = useMutation<SmartTranscribeResponse, Error, void>({
    mutationFn: () => smartTranscribe(url, language),
  });
  const metadataMutation = useMutation<YouTubeMetadata, Error, void>({
    mutationFn: () => getMetadata(url),
  });
  const playlistMutation = useMutation<PlaylistTranscribeResponse, Error, void>({
    mutationFn: () => transcribePlaylist(url, language),
  });
  const chapterMutation = useMutation<AutoChapterResponse, Error, void>({
    mutationFn: () => autoChapter(url),
  });

  const isLoading = smartMutation.isPending || metadataMutation.isPending || playlistMutation.isPending || chapterMutation.isPending;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 1 }}>YouTube Studio</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Smart transcription, metadata extraction, playlist processing, and auto-chaptering
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={8}>
              <TextField fullWidth value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://youtube.com/watch?v=... or playlist URL" label="YouTube URL" />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField fullWidth select value={language} onChange={(e) => setLanguage(e.target.value)} label="Language" SelectProps={{ native: true }}>
                <option value="auto">Auto-detect</option>
                <option value="fr">French</option>
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="de">German</option>
                <option value="ar">Arabic</option>
              </TextField>
            </Grid>
          </Grid>

          <Tabs value={tab} onChange={(_, v: number) => setTab(v)} sx={{ mb: 2 }}>
            <Tab label="Smart Transcribe" />
            <Tab label="Metadata" />
            <Tab label="Playlist Bulk" />
            <Tab label="Auto-Chapter" />
          </Tabs>

          {tab === 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Automatically uses the best provider: YouTube subtitles (free) &gt; Whisper (local) &gt; AssemblyAI
              </Typography>
              <Button variant="contained" onClick={() => smartMutation.mutate()} disabled={!url.trim() || isLoading}>
                {smartMutation.isPending ? <><CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />Transcribing...</> : 'Smart Transcribe'}
              </Button>
            </Box>
          )}

          {tab === 1 && (
            <Button variant="contained" onClick={() => metadataMutation.mutate()} disabled={!url.trim() || isLoading}>
              {metadataMutation.isPending ? <><CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />Extracting...</> : 'Extract Metadata'}
            </Button>
          )}

          {tab === 2 && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Transcribe all videos in a playlist or channel (max 100 videos)
              </Typography>
              <Button variant="contained" color="secondary" onClick={() => playlistMutation.mutate()} disabled={!url.trim() || isLoading}>
                {playlistMutation.isPending ? <><CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />Processing...</> : 'Transcribe Playlist'}
              </Button>
            </Box>
          )}

          {tab === 3 && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Combine YouTube chapters with AI summaries for each section
              </Typography>
              <Button variant="contained" color="warning" onClick={() => chapterMutation.mutate()} disabled={!url.trim() || isLoading}>
                {chapterMutation.isPending ? <><CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />Analyzing...</> : 'Auto-Chapter'}
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Smart Transcribe Result */}
      {smartMutation.data && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', gap: 1, mb: 2, alignItems: 'center' }}>
              <Typography variant="h6">Transcription Result</Typography>
              <ProviderChip provider={smartMutation.data.provider} />
              {smartMutation.data.is_manual && <Chip label="Manual subs" size="small" color="info" />}
              <Chip label={`${formatDuration(smartMutation.data.duration_seconds)}`} size="small" variant="outlined" />
              <Chip label={`${smartMutation.data.language}`} size="small" variant="outlined" />
            </Box>
            <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1, maxHeight: 400, overflow: 'auto' }}>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                {smartMutation.data.text}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Metadata Result */}
      {metadataMutation.data && <Box sx={{ mb: 3 }}><MetadataCard data={metadataMutation.data} /></Box>}

      {/* Playlist Result */}
      {playlistMutation.data?.success && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
              <Typography variant="h6">Playlist Results</Typography>
              <Chip label={`${playlistMutation.data.transcribed}/${playlistMutation.data.total} transcribed`} color="primary" />
            </Box>
            <List>
              {playlistMutation.data.results.map((r) => (
                <ListItem key={r.video_id} divider sx={{ alignItems: 'flex-start' }}>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>{r.title || r.video_id}</Typography>
                        <ProviderChip provider={r.provider} />
                        {r.success ? <Chip label="OK" size="small" color="success" /> : <Chip label="Failed" size="small" color="error" />}
                      </Box>
                    }
                    secondary={r.success ? r.transcript : r.error}
                    secondaryTypographyProps={{ variant: 'caption', sx: { maxHeight: 60, overflow: 'hidden' } }}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Chapter Result */}
      {chapterMutation.data && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>{chapterMutation.data.title}</Typography>
            <ProviderChip provider={chapterMutation.data.provider} />

            {chapterMutation.data.full_summary && (
              <Box sx={{ mt: 2, p: 2, bgcolor: 'primary.50', borderRadius: 1, border: '1px solid', borderColor: 'primary.200' }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Overall Summary</Typography>
                <Typography variant="body2">{chapterMutation.data.full_summary}</Typography>
              </Box>
            )}

            <Divider sx={{ my: 2 }} />

            {chapterMutation.data.chapters.map((ch, i) => (
              <Box key={i} sx={{ mb: 2, p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                <Box sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                  <Chip label={formatDuration(Math.round(ch.start_time))} size="small" variant="outlined" />
                  <Typography variant="subtitle2">{ch.title}</Typography>
                </Box>
                {ch.summary && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{ch.summary}</Typography>
                )}
              </Box>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Errors */}
      {smartMutation.isError && <Alert severity="error" sx={{ mb: 2 }}>{smartMutation.error.message}</Alert>}
      {metadataMutation.isError && <Alert severity="error" sx={{ mb: 2 }}>{metadataMutation.error.message}</Alert>}
      {playlistMutation.isError && <Alert severity="error" sx={{ mb: 2 }}>{playlistMutation.error.message}</Alert>}
      {chapterMutation.isError && <Alert severity="error" sx={{ mb: 2 }}>{chapterMutation.error.message}</Alert>}
    </Box>
  );
}
