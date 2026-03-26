'use client';

import { useCallback, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Slider,
  Tab,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import AudiotrackIcon from '@mui/icons-material/Audiotrack';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import ContentCutIcon from '@mui/icons-material/ContentCut';
import DeleteIcon from '@mui/icons-material/Delete';
import DescriptionIcon from '@mui/icons-material/Description';
import DownloadIcon from '@mui/icons-material/Download';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';
import ListAltIcon from '@mui/icons-material/ListAlt';
import MicIcon from '@mui/icons-material/Mic';
import PodcastsIcon from '@mui/icons-material/Podcasts';
import SpeedIcon from '@mui/icons-material/Speed';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';

import {
  useAudioList,
  useCreateEpisode,
  useDeleteAudio,
  useEditAudio,
  useEpisodeList,
  useGenerateChapters,
  useGenerateShowNotes,
  useSplitAudio,
  useTranscribeAudio,
  useUploadAudio,
} from '@/features/audio-studio/hooks/useAudioStudio';
import { getExportUrl } from '@/features/audio-studio/api';
import type { AudioFile, Chapter, AudioEditOperation } from '@/features/audio-studio/types';

const STATUS_COLORS: Record<string, 'default' | 'success' | 'error' | 'info' | 'warning'> = {
  uploading: 'info',
  ready: 'success',
  processing: 'warning',
  failed: 'error',
};

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function formatSize(kb: number): string {
  if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`;
  return `${kb} KB`;
}

/* ========================================================================
   Mini Waveform Component
   ======================================================================== */

function MiniWaveform({ data }: { data: number[] | null }) {
  if (!data || data.length === 0) return null;
  const step = Math.max(1, Math.floor(data.length / 80));
  const bars = [];
  for (let i = 0; i < data.length; i += step) {
    bars.push(data[i]);
  }
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: '1px', height: 32 }}>
      {bars.slice(0, 80).map((v, i) => (
        <Box
          key={i}
          sx={{
            width: 2,
            height: `${Math.max(4, (v ?? 0) * 32)}px`,
            bgcolor: 'primary.main',
            borderRadius: 1,
            opacity: 0.7,
          }}
        />
      ))}
    </Box>
  );
}

/* ========================================================================
   Main Page
   ======================================================================== */

export default function AudioStudioPage() {
  const { data: audioFiles, isLoading } = useAudioList();
  const { data: episodes } = useEpisodeList();
  const uploadMutation = useUploadAudio();
  const deleteMutation = useDeleteAudio();
  const transcribeMutation = useTranscribeAudio();
  const chaptersMutation = useGenerateChapters();
  const showNotesMutation = useGenerateShowNotes();
  const editMutation = useEditAudio();
  const splitMutation = useSplitAudio();
  const createEpisodeMutation = useCreateEpisode();

  const [tab, setTab] = useState(0);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [selected, setSelected] = useState<AudioFile | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [episodeDialogOpen, setEpisodeDialogOpen] = useState(false);
  const [episodeTitle, setEpisodeTitle] = useState('');
  const [episodeDescription, setEpisodeDescription] = useState('');
  const [exportFormat, setExportFormat] = useState('mp3');

  // Edit state
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(0);
  const [fadeDuration, setFadeDuration] = useState(2);
  const [speedFactor, setSpeedFactor] = useState(1.0);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadProgress(0);
    uploadMutation.mutate(
      { file, onProgress: setUploadProgress },
      { onSettled: () => setUploadProgress(null) },
    );
    e.target.value = '';
  }, [uploadMutation]);

  const handleEdit = (opType: AudioEditOperation['type'], params: Record<string, unknown> = {}) => {
    if (!selected) return;
    editMutation.mutate({ id: selected.id, data: { operations: [{ type: opType, params }] } });
    setEditDialogOpen(false);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AudiotrackIcon color="primary" /> Audio Studio
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Podcast and audio editing studio with AI-powered chapters, transcription, and RSS feed
        </Typography>
      </Box>

      {/* Tabs */}
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab icon={<GraphicEqIcon />} label="Audio Files" />
        <Tab icon={<PodcastsIcon />} label="Podcast Episodes" />
      </Tabs>

      {/* ============================================================
          TAB 0: Audio Files
          ============================================================ */}
      {tab === 0 && (
        <Grid container spacing={3}>
          {/* Upload + Actions Panel */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>Upload Audio</Typography>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".mp3,.wav,.ogg,.flac,.m4a,.aac,.webm,.mp4,.wma"
                  hidden
                  onChange={handleUpload}
                />
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<CloudUploadIcon />}
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadMutation.isPending}
                  sx={{ mb: 2 }}
                >
                  {uploadMutation.isPending ? 'Uploading...' : 'Choose Audio File'}
                </Button>
                {uploadProgress !== null && (
                  <LinearProgress variant="determinate" value={uploadProgress} sx={{ mb: 2 }} />
                )}

                {uploadMutation.isError && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    Upload failed: {uploadMutation.error.message}
                  </Alert>
                )}

                <Divider sx={{ my: 2 }} />

                {/* Quick actions on selected file */}
                {selected && (
                  <>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>
                      Selected: {selected.filename}
                    </Typography>

                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<MicIcon />}
                        onClick={() => transcribeMutation.mutate(selected.id)}
                        disabled={transcribeMutation.isPending}
                      >
                        Transcribe
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<ListAltIcon />}
                        onClick={() => chaptersMutation.mutate(selected.id)}
                        disabled={chaptersMutation.isPending}
                      >
                        Chapters
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<DescriptionIcon />}
                        onClick={() => showNotesMutation.mutate(selected.id)}
                        disabled={showNotesMutation.isPending}
                      >
                        Show Notes
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<ContentCutIcon />}
                        onClick={() => splitMutation.mutate({ id: selected.id })}
                        disabled={splitMutation.isPending}
                      >
                        Split
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<SpeedIcon />}
                        onClick={() => setEditDialogOpen(true)}
                      >
                        Edit
                      </Button>
                    </Box>

                    {/* Export */}
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <FormControl size="small" sx={{ minWidth: 80 }}>
                        <InputLabel>Format</InputLabel>
                        <Select value={exportFormat} label="Format" onChange={(e) => setExportFormat(e.target.value)}>
                          <MenuItem value="mp3">MP3</MenuItem>
                          <MenuItem value="wav">WAV</MenuItem>
                          <MenuItem value="ogg">OGG</MenuItem>
                          <MenuItem value="flac">FLAC</MenuItem>
                        </Select>
                      </FormControl>
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<DownloadIcon />}
                        href={getExportUrl(selected.id, exportFormat)}
                        target="_blank"
                      >
                        Export
                      </Button>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    {/* Create Episode */}
                    <Button
                      fullWidth
                      variant="contained"
                      color="secondary"
                      startIcon={<PodcastsIcon />}
                      onClick={() => {
                        setEpisodeTitle('');
                        setEpisodeDescription('');
                        setEpisodeDialogOpen(true);
                      }}
                    >
                      Create Episode
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Show notes result */}
            {showNotesMutation.data && (
              <Card sx={{ mt: 2 }}>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 1 }}>Show Notes</Typography>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    {showNotesMutation.data.show_notes.summary}
                  </Typography>
                  {showNotesMutation.data.show_notes.key_points.length > 0 && (
                    <>
                      <Typography variant="subtitle2">Key Points:</Typography>
                      <ul>
                        {showNotesMutation.data.show_notes.key_points.map((p, i) => (
                          <li key={i}><Typography variant="body2">{p}</Typography></li>
                        ))}
                      </ul>
                    </>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Split result */}
            {splitMutation.data && (
              <Card sx={{ mt: 2 }}>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    Split Result ({splitMutation.data.count} segments)
                  </Typography>
                  {splitMutation.data.segments.map((seg) => (
                    <Typography key={seg.index} variant="body2">
                      Segment {seg.index + 1}: {formatDuration(seg.start_seconds)} - {formatDuration(seg.end_seconds)} ({formatDuration(seg.duration_seconds)})
                    </Typography>
                  ))}
                </CardContent>
              </Card>
            )}
          </Grid>

          {/* Audio List */}
          <Grid item xs={12} md={8}>
            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
                <CircularProgress />
              </Box>
            ) : !audioFiles?.length ? (
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 6 }}>
                  <AudiotrackIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">No audio files yet</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Upload your first audio file to get started
                  </Typography>
                </CardContent>
              </Card>
            ) : (
              audioFiles.map((audio) => (
                <Card
                  key={audio.id}
                  sx={{
                    mb: 2,
                    cursor: 'pointer',
                    border: selected?.id === audio.id ? 2 : 0,
                    borderColor: 'primary.main',
                  }}
                  onClick={() => setSelected(audio)}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Box sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <AudiotrackIcon fontSize="small" color="primary" />
                          <Typography variant="subtitle1" fontWeight={600}>
                            {audio.filename}
                          </Typography>
                          <Chip
                            label={audio.status}
                            size="small"
                            color={STATUS_COLORS[audio.status] || 'default'}
                          />
                        </Box>

                        <Typography variant="body2" color="text.secondary">
                          {formatDuration(audio.duration_seconds)} | {audio.sample_rate} Hz | {audio.channels}ch | {audio.format.toUpperCase()} | {formatSize(audio.file_size_kb)}
                        </Typography>

                        <MiniWaveform data={audio.waveform_data} />

                        {/* Chapters */}
                        {audio.chapters.length > 0 && (
                          <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                            {audio.chapters.map((ch: Chapter, i: number) => (
                              <Chip
                                key={i}
                                label={`${ch.title} (${formatDuration(ch.start_time)})`}
                                size="small"
                                variant="outlined"
                              />
                            ))}
                          </Box>
                        )}

                        {/* Transcript snippet */}
                        {audio.transcript && (
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }} noWrap>
                            {audio.transcript.slice(0, 150)}...
                          </Typography>
                        )}
                      </Box>

                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteMutation.mutate(audio.id);
                            if (selected?.id === audio.id) setSelected(null);
                          }}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </CardContent>
                </Card>
              ))
            )}
          </Grid>
        </Grid>
      )}

      {/* ============================================================
          TAB 1: Podcast Episodes
          ============================================================ */}
      {tab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            {!episodes?.length ? (
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 6 }}>
                  <PodcastsIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">No episodes yet</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Select an audio file and create your first podcast episode
                  </Typography>
                </CardContent>
              </Card>
            ) : (
              episodes.map((ep) => (
                <Card key={ep.id} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <PodcastsIcon color="secondary" />
                      <Typography variant="h6">{ep.title}</Typography>
                      <Chip
                        label={ep.is_published ? 'Published' : 'Draft'}
                        size="small"
                        color={ep.is_published ? 'success' : 'default'}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {ep.description || 'No description'}
                    </Typography>
                    {ep.publish_date && (
                      <Typography variant="caption" color="text.secondary">
                        Published: {new Date(ep.publish_date).toLocaleDateString()}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </Grid>
        </Grid>
      )}

      {/* ============================================================
          EDIT DIALOG
          ============================================================ */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Audio</DialogTitle>
        <DialogContent>
          {selected && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                {selected.filename} ({formatDuration(selected.duration_seconds)})
              </Typography>

              {/* Trim */}
              <Typography variant="body2" fontWeight={600}>Trim</Typography>
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <TextField
                  size="small"
                  label="Start (s)"
                  type="number"
                  value={trimStart}
                  onChange={(e) => setTrimStart(Number(e.target.value))}
                />
                <TextField
                  size="small"
                  label="End (s)"
                  type="number"
                  value={trimEnd || selected.duration_seconds}
                  onChange={(e) => setTrimEnd(Number(e.target.value))}
                />
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => handleEdit('trim', { start: trimStart, end: trimEnd || selected.duration_seconds })}
                >
                  Trim
                </Button>
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Fade */}
              <Typography variant="body2" fontWeight={600}>Fade (seconds)</Typography>
              <Slider
                value={fadeDuration}
                min={0.5}
                max={10}
                step={0.5}
                valueLabelDisplay="auto"
                onChange={(_, v) => setFadeDuration(v as number)}
                sx={{ mb: 1, maxWidth: 300 }}
              />
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Button variant="outlined" size="small" onClick={() => handleEdit('fade_in', { duration: fadeDuration })}>
                  Fade In
                </Button>
                <Button variant="outlined" size="small" onClick={() => handleEdit('fade_out', { duration: fadeDuration })}>
                  Fade Out
                </Button>
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Speed */}
              <Typography variant="body2" fontWeight={600}>Speed: {speedFactor}x</Typography>
              <Slider
                value={speedFactor}
                min={0.5}
                max={3.0}
                step={0.1}
                valueLabelDisplay="auto"
                onChange={(_, v) => setSpeedFactor(v as number)}
                sx={{ mb: 1, maxWidth: 300 }}
              />
              <Button variant="outlined" size="small" onClick={() => handleEdit('speed_change', { factor: speedFactor })} sx={{ mb: 2 }}>
                Apply Speed
              </Button>

              <Divider sx={{ my: 2 }} />

              {/* One-click operations */}
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Button variant="contained" size="small" startIcon={<VolumeUpIcon />} onClick={() => handleEdit('normalize')}>
                  Normalize
                </Button>
                <Button variant="contained" size="small" onClick={() => handleEdit('noise_reduction')}>
                  Noise Reduction
                </Button>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* ============================================================
          CREATE EPISODE DIALOG
          ============================================================ */}
      <Dialog open={episodeDialogOpen} onClose={() => setEpisodeDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Podcast Episode</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Episode Title"
            value={episodeTitle}
            onChange={(e) => setEpisodeTitle(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Description"
            value={episodeDescription}
            onChange={(e) => setEpisodeDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEpisodeDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            disabled={!episodeTitle.trim() || !selected || createEpisodeMutation.isPending}
            onClick={() => {
              if (!selected) return;
              createEpisodeMutation.mutate(
                {
                  title: episodeTitle,
                  description: episodeDescription,
                  audio_id: selected.id,
                },
                { onSuccess: () => { setEpisodeDialogOpen(false); setTab(1); } },
              );
            }}
          >
            {createEpisodeMutation.isPending ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Loading overlays for mutations */}
      {(transcribeMutation.isPending || chaptersMutation.isPending || editMutation.isPending) && (
        <Box sx={{ position: 'fixed', bottom: 24, right: 24, zIndex: 9999 }}>
          <Card sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <CircularProgress size={24} />
            <Typography variant="body2">
              {transcribeMutation.isPending && 'Transcribing...'}
              {chaptersMutation.isPending && 'Generating chapters...'}
              {editMutation.isPending && 'Applying edits...'}
            </Typography>
          </Card>
        </Box>
      )}
    </Box>
  );
}
