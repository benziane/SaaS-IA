'use client';

import { useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  Dialog, DialogActions, DialogContent, DialogTitle,
  FormControl, Grid, InputLabel, MenuItem, Select,
  Skeleton, TextField, Typography,
} from '@mui/material';
import ImageIcon from '@mui/icons-material/Image';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import DeleteIcon from '@mui/icons-material/Delete';
import IconButton from '@mui/material/IconButton';

import { useDeleteImage, useGenerateImage, useImages } from '@/features/image-gen/hooks/useImageGen';

const STYLES = [
  { id: 'realistic', label: 'Realistic', icon: '📷' },
  { id: 'artistic', label: 'Artistic', icon: '🎨' },
  { id: 'cartoon', label: 'Cartoon', icon: '🖍️' },
  { id: 'digital_art', label: 'Digital Art', icon: '💠' },
  { id: 'photography', label: 'Photography', icon: '📸' },
  { id: '3d_render', label: '3D Render', icon: '🧊' },
  { id: 'minimalist', label: 'Minimalist', icon: '⬜' },
  { id: 'watercolor', label: 'Watercolor', icon: '🌊' },
];

const STATUS_COLORS: Record<string, 'default' | 'info' | 'success' | 'error'> = {
  pending: 'default', generating: 'info', completed: 'success', failed: 'error',
};

export default function ImagesPage() {
  const { data: images, isLoading } = useImages();
  const genMutation = useGenerateImage();
  const deleteMutation = useDeleteImage();

  const [prompt, setPrompt] = useState('');
  const [negPrompt, setNegPrompt] = useState('');
  const [style, setStyle] = useState('digital_art');
  const [width, setWidth] = useState(1024);
  const [height, setHeight] = useState(1024);

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    genMutation.mutate({ prompt, negative_prompt: negPrompt || undefined, style, width, height });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ImageIcon color="primary" /> Image Studio
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Generate AI images, thumbnails, and visual content
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Generate Image</Typography>
              <TextField fullWidth multiline rows={4} label="Prompt" placeholder="Describe the image you want to create..."
                value={prompt} onChange={(e) => setPrompt(e.target.value)} sx={{ mb: 2 }} />
              <TextField fullWidth size="small" label="Negative prompt (optional)" placeholder="What to avoid..."
                value={negPrompt} onChange={(e) => setNegPrompt(e.target.value)} sx={{ mb: 2 }} />

              <Typography variant="subtitle2" sx={{ mb: 1 }}>Style</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                {STYLES.map((s) => (
                  <Chip key={s.id} label={`${s.icon} ${s.label}`} size="small"
                    variant={style === s.id ? 'filled' : 'outlined'}
                    color={style === s.id ? 'primary' : 'default'}
                    onClick={() => setStyle(s.id)} />
                ))}
              </Box>

              <Grid container spacing={1} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Width</InputLabel>
                    <Select value={width} label="Width" onChange={(e) => setWidth(Number(e.target.value))}>
                      {[512, 768, 1024, 1280, 1536, 1920].map((w) => <MenuItem key={w} value={w}>{w}px</MenuItem>)}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Height</InputLabel>
                    <Select value={height} label="Height" onChange={(e) => setHeight(Number(e.target.value))}>
                      {[512, 768, 1024, 1280, 1536, 1920].map((h) => <MenuItem key={h} value={h}>{h}px</MenuItem>)}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>

              <Button variant="contained" fullWidth onClick={handleGenerate}
                disabled={!prompt.trim() || genMutation.isPending}
                startIcon={genMutation.isPending ? <CircularProgress size={18} color="inherit" /> : <AutoAwesomeIcon />}>
                {genMutation.isPending ? 'Generating...' : 'Generate Image'}
              </Button>
              {genMutation.isError && <Alert severity="error" sx={{ mt: 2 }}>{genMutation.error.message}</Alert>}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Gallery</Typography>
              {isLoading ? <Skeleton variant="rectangular" height={400} /> : !images?.length ? (
                <Box sx={{ textAlign: 'center', py: 6 }}>
                  <ImageIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 1 }} />
                  <Typography color="text.secondary">No images yet. Generate your first one!</Typography>
                </Box>
              ) : (
                <Grid container spacing={1.5}>
                  {images.map((img) => (
                    <Grid item xs={6} sm={4} key={img.id}>
                      <Card variant="outlined" sx={{ position: 'relative' }}>
                        <Box sx={{ height: 160, bgcolor: 'action.hover', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          {img.status === 'completed' ? (
                            <Typography variant="caption" sx={{ p: 1, textAlign: 'center' }}>{img.prompt.substring(0, 60)}...</Typography>
                          ) : img.status === 'generating' ? (
                            <CircularProgress size={24} />
                          ) : (
                            <Typography color="error" variant="caption">Failed</Typography>
                          )}
                        </Box>
                        <Box sx={{ p: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Box sx={{ display: 'flex', gap: 0.5 }}>
                            <Chip label={img.style} size="small" variant="outlined" />
                            <Chip label={img.status} size="small" color={STATUS_COLORS[img.status] || 'default'} />
                          </Box>
                          <IconButton size="small" color="error" onClick={() => deleteMutation.mutate(img.id)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Box>
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
