'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
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
  MenuItem,
  Select,
  Skeleton,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SlideshowIcon from '@mui/icons-material/Slideshow';
import DownloadIcon from '@mui/icons-material/Download';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

import {
  useCreatePresentation,
  useDeletePresentation,
  useExportPresentation,
  usePresentations,
} from '@/features/presentation-gen/hooks/usePresentationGen';
import type { Presentation, SlideContent } from '@/features/presentation-gen/types';

const TEMPLATE_OPTIONS = [
  { id: 'default', label: 'Default' },
  { id: 'pitch_deck', label: 'Pitch Deck' },
  { id: 'report', label: 'Report' },
  { id: 'tutorial', label: 'Tutorial' },
  { id: 'meeting', label: 'Meeting' },
  { id: 'proposal', label: 'Proposal' },
];

const STYLE_OPTIONS = ['professional', 'creative', 'minimal', 'corporate', 'academic', 'dark', 'colorful'];

const STATUS_COLORS: Record<string, 'default' | 'success' | 'error' | 'info'> = {
  generating: 'info',
  ready: 'success',
  error: 'error',
};

export default function PresentationsPage() {
  const { data: presentations, isLoading } = usePresentations();
  const createMutation = useCreatePresentation();
  const deleteMutation = useDeletePresentation();

  // Create dialog state
  const [createOpen, setCreateOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [topic, setTopic] = useState('');
  const [numSlides, setNumSlides] = useState(10);
  const [style, setStyle] = useState('professional');
  const [template, setTemplate] = useState('default');
  const [language, setLanguage] = useState('fr');
  const [sourceText, setSourceText] = useState('');

  // Viewer state
  const [activePresentation, setActivePresentation] = useState<Presentation | null>(null);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [exportOpen, setExportOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState<'html' | 'markdown' | 'pdf'>('html');

  const exportMutation = useExportPresentation(activePresentation?.id || '');

  const handleCreate = () => {
    if (!title.trim() || !topic.trim()) return;
    createMutation.mutate(
      {
        title,
        topic,
        num_slides: numSlides,
        style,
        template,
        language,
        source_text: sourceText || undefined,
      },
      {
        onSuccess: (pres) => {
          setCreateOpen(false);
          setTitle('');
          setTopic('');
          setSourceText('');
          setActivePresentation(pres);
          setCurrentSlide(0);
        },
      },
    );
  };

  const handleExport = () => {
    exportMutation.mutate(
      { format: exportFormat },
      {
        onSuccess: (result) => {
          if (result.content) {
            const blob = new Blob([result.content], {
              type: exportFormat === 'html' ? 'text/html' : 'text/markdown',
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = result.filename;
            a.click();
            URL.revokeObjectURL(url);
          }
          setExportOpen(false);
        },
      },
    );
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const slides: SlideContent[] = activePresentation?.slides || [];
  const slide = slides[currentSlide] || null;

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SlideshowIcon color="primary" /> Presentations
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Generate AI-powered slide decks from topics, text, or transcriptions
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
          New Presentation
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Presentations List */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                My Presentations
              </Typography>
              {isLoading ? (
                <Skeleton variant="rectangular" height={200} />
              ) : !presentations?.length ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <SlideshowIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                  <Typography color="text.secondary">No presentations yet</Typography>
                  <Button size="small" onClick={() => setCreateOpen(true)} sx={{ mt: 1 }}>
                    Create your first presentation
                  </Button>
                </Box>
              ) : (
                presentations.map((pres) => (
                  <Card
                    key={pres.id}
                    variant="outlined"
                    sx={{
                      mb: 1,
                      cursor: 'pointer',
                      bgcolor: activePresentation?.id === pres.id ? 'action.selected' : 'transparent',
                      '&:hover': { bgcolor: 'action.hover' },
                    }}
                    onClick={() => {
                      setActivePresentation(pres);
                      setCurrentSlide(0);
                    }}
                  >
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="subtitle2">{pres.title}</Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                        {pres.topic.substring(0, 80)}{pres.topic.length > 80 ? '...' : ''}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap' }}>
                        <Chip label={pres.template} size="small" variant="outlined" />
                        <Chip label={`${pres.num_slides} slides`} size="small" variant="outlined" />
                        <Chip
                          label={pres.status}
                          size="small"
                          color={STATUS_COLORS[pres.status] || 'default'}
                        />
                      </Box>
                    </CardContent>
                    <CardActions sx={{ pt: 0, justifyContent: 'flex-end' }}>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteMutation.mutate(pres.id);
                          if (activePresentation?.id === pres.id) setActivePresentation(null);
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </CardActions>
                  </Card>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Slide Viewer */}
        <Grid item xs={12} md={8}>
          {activePresentation && slide ? (
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6">{activePresentation.title}</Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Tooltip title="Export">
                      <IconButton size="small" onClick={() => setExportOpen(true)}>
                        <DownloadIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Copy slide content">
                      <IconButton size="small" onClick={() => handleCopy(slide.content)}>
                        <ContentCopyIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>

                {/* Slide display */}
                <Card
                  variant="outlined"
                  sx={{
                    minHeight: 400,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    p: 4,
                    bgcolor: 'grey.50',
                  }}
                >
                  <Typography
                    variant={slide.layout === 'title_slide' ? 'h3' : 'h5'}
                    sx={{
                      mb: 2,
                      textAlign: slide.layout === 'title_slide' || slide.layout === 'section_header' ? 'center' : 'left',
                      fontWeight: 'bold',
                    }}
                  >
                    {slide.title}
                  </Typography>
                  <Typography
                    variant="body1"
                    sx={{
                      whiteSpace: 'pre-wrap',
                      lineHeight: 1.8,
                      textAlign: slide.layout === 'quote' ? 'center' : 'left',
                      fontStyle: slide.layout === 'quote' ? 'italic' : 'normal',
                    }}
                  >
                    {slide.content}
                  </Typography>
                  {slide.notes && (
                    <Box sx={{ mt: 3, pt: 2, borderTop: '1px dashed', borderColor: 'divider' }}>
                      <Typography variant="caption" color="text.secondary">
                        Speaker notes: {slide.notes}
                      </Typography>
                    </Box>
                  )}
                </Card>

                {/* Navigation */}
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2, mt: 2 }}>
                  <IconButton
                    onClick={() => setCurrentSlide((prev) => Math.max(0, prev - 1))}
                    disabled={currentSlide === 0}
                  >
                    <NavigateBeforeIcon />
                  </IconButton>
                  <Typography variant="body2" color="text.secondary">
                    Slide {currentSlide + 1} / {slides.length}
                  </Typography>
                  <IconButton
                    onClick={() => setCurrentSlide((prev) => Math.min(slides.length - 1, prev + 1))}
                    disabled={currentSlide === slides.length - 1}
                  >
                    <NavigateNextIcon />
                  </IconButton>
                </Box>

                {/* Slide thumbnails */}
                <Box sx={{ display: 'flex', gap: 1, mt: 2, overflowX: 'auto', pb: 1 }}>
                  {slides.map((s, idx) => (
                    <Chip
                      key={idx}
                      label={`${idx + 1}. ${s.title.substring(0, 20)}${s.title.length > 20 ? '...' : ''}`}
                      size="small"
                      variant={idx === currentSlide ? 'filled' : 'outlined'}
                      color={idx === currentSlide ? 'primary' : 'default'}
                      onClick={() => setCurrentSlide(idx)}
                      sx={{ flexShrink: 0 }}
                    />
                  ))}
                </Box>

                <Divider sx={{ my: 2 }} />
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Template: {activePresentation.template}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Style: {activePresentation.style}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Layout: {slide.layout}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <SlideshowIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Select a presentation or create a new one
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Enter a topic, choose a template, and let AI generate your slide deck
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Create Presentation Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>New Presentation</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Title"
            placeholder="e.g., Introduction to AI in Healthcare"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Topic / Description"
            placeholder="Describe the subject, key points, and goals for this presentation"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Source Text (optional)"
            placeholder="Paste any reference material, article, or notes to base the presentation on"
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Slides"
                value={numSlides}
                onChange={(e) => setNumSlides(Math.max(3, Math.min(50, parseInt(e.target.value) || 10)))}
                inputProps={{ min: 3, max: 50 }}
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Template</InputLabel>
                <Select value={template} label="Template" onChange={(e) => setTemplate(e.target.value)}>
                  {TEMPLATE_OPTIONS.map((t) => (
                    <MenuItem key={t.id} value={t.id}>
                      {t.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6} sm={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Style</InputLabel>
                <Select value={style} label="Style" onChange={(e) => setStyle(e.target.value)}>
                  {STYLE_OPTIONS.map((s) => (
                    <MenuItem key={s} value={s}>
                      {s.charAt(0).toUpperCase() + s.slice(1)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6} sm={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Language</InputLabel>
                <Select value={language} label="Language" onChange={(e) => setLanguage(e.target.value)}>
                  <MenuItem value="fr">French</MenuItem>
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="es">Spanish</MenuItem>
                  <MenuItem value="de">German</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!title.trim() || !topic.trim() || createMutation.isPending}
            startIcon={createMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <SlideshowIcon />}
          >
            {createMutation.isPending ? 'Generating...' : 'Generate Presentation'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={exportOpen} onClose={() => setExportOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Export Presentation</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel>Format</InputLabel>
            <Select
              value={exportFormat}
              label="Format"
              onChange={(e) => setExportFormat(e.target.value as 'html' | 'markdown' | 'pdf')}
            >
              <MenuItem value="html">HTML (interactive)</MenuItem>
              <MenuItem value="markdown">Markdown</MenuItem>
              <MenuItem value="pdf">PDF (requires marp-cli)</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleExport}
            disabled={exportMutation.isPending}
            startIcon={exportMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <DownloadIcon />}
          >
            {exportMutation.isPending ? 'Exporting...' : 'Export'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Errors */}
      {createMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {createMutation.error?.message}
        </Alert>
      )}
      {exportMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {exportMutation.error?.message}
        </Alert>
      )}
    </Box>
  );
}
