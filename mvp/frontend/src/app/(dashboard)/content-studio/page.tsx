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
  Tab,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import ArticleIcon from '@mui/icons-material/Article';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

import {
  useCreateProject,
  useDeleteProject,
  useGenerateContents,
  useProjectContents,
  useProjects,
  useRegenerateContent,
} from '@/features/content-studio/hooks/useContentStudio';
import type { GeneratedContent } from '@/features/content-studio/types';

const FORMAT_OPTIONS = [
  { id: 'blog_article', label: 'Blog Article', icon: '📝' },
  { id: 'twitter_thread', label: 'Twitter/X Thread', icon: '🐦' },
  { id: 'linkedin_post', label: 'LinkedIn Post', icon: '💼' },
  { id: 'newsletter', label: 'Newsletter', icon: '📧' },
  { id: 'instagram_carousel', label: 'Instagram Carousel', icon: '📸' },
  { id: 'youtube_description', label: 'YouTube Description', icon: '🎬' },
  { id: 'seo_meta', label: 'SEO Metadata', icon: '🔍' },
  { id: 'press_release', label: 'Press Release', icon: '📰' },
  { id: 'email_campaign', label: 'Email Campaign', icon: '📨' },
  { id: 'podcast_notes', label: 'Podcast Notes', icon: '🎙️' },
];

const STATUS_COLORS: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning' | 'info'> = {
  draft: 'default',
  generating: 'info',
  generated: 'success',
  published: 'primary',
  scheduled: 'warning',
  failed: 'error',
};

const TONE_OPTIONS = ['professional', 'casual', 'engaging', 'formal', 'humorous', 'inspirational', 'educational'];

export default function ContentStudioPage() {
  const { data: projects, isLoading } = useProjects();
  const createMutation = useCreateProject();
  const deleteMutation = useDeleteProject();

  const [createOpen, setCreateOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [sourceText, setSourceText] = useState('');
  const [tone, setTone] = useState('professional');
  const [audience, setAudience] = useState('');
  const [selectedFormats, setSelectedFormats] = useState<string[]>(['blog_article', 'twitter_thread', 'linkedin_post']);

  const [activeProject, setActiveProject] = useState<string | null>(null);
  const [viewContent, setViewContent] = useState<GeneratedContent | null>(null);

  const { data: contents, isLoading: contentsLoading } = useProjectContents(activeProject);
  const generateMutation = useGenerateContents(activeProject || '');
  const regenerateMutation = useRegenerateContent();

  const handleCreate = () => {
    if (!title.trim() || !sourceText.trim()) return;
    createMutation.mutate(
      {
        title,
        source_type: 'text',
        source_text: sourceText,
        tone,
        target_audience: audience || undefined,
      },
      {
        onSuccess: (project) => {
          setCreateOpen(false);
          setTitle('');
          setSourceText('');
          setActiveProject(project.id);
          // Auto-generate
          generateMutation.mutate({ formats: selectedFormats });
        },
      }
    );
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AutoAwesomeIcon color="primary" /> Content Studio
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Transform any content into blog articles, social media posts, newsletters, and more
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
          New Project
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Projects List */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Projects</Typography>
              {isLoading ? (
                <Skeleton variant="rectangular" height={200} />
              ) : !projects?.length ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <ArticleIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                  <Typography color="text.secondary">No projects yet</Typography>
                  <Button size="small" onClick={() => setCreateOpen(true)} sx={{ mt: 1 }}>
                    Create your first project
                  </Button>
                </Box>
              ) : (
                projects.map((project) => (
                  <Card
                    key={project.id}
                    variant="outlined"
                    sx={{
                      mb: 1,
                      cursor: 'pointer',
                      bgcolor: activeProject === project.id ? 'action.selected' : 'transparent',
                      '&:hover': { bgcolor: 'action.hover' },
                    }}
                    onClick={() => setActiveProject(project.id)}
                  >
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="subtitle2">{project.title}</Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                        <Chip label={project.source_type} size="small" variant="outlined" />
                        <Chip label={project.tone} size="small" color="primary" variant="outlined" />
                      </Box>
                    </CardContent>
                    <CardActions sx={{ pt: 0, justifyContent: 'flex-end' }}>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteMutation.mutate(project.id);
                          if (activeProject === project.id) setActiveProject(null);
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

        {/* Generated Contents */}
        <Grid item xs={12} md={8}>
          {activeProject ? (
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6">Generated Content</Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={generateMutation.isPending ? <CircularProgress size={16} /> : <AutoAwesomeIcon />}
                    onClick={() => generateMutation.mutate({ formats: selectedFormats })}
                    disabled={generateMutation.isPending}
                  >
                    {generateMutation.isPending ? 'Generating...' : 'Generate More'}
                  </Button>
                </Box>

                {/* Format selector for generation */}
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                  {FORMAT_OPTIONS.map((fmt) => (
                    <Chip
                      key={fmt.id}
                      label={`${fmt.icon} ${fmt.label}`}
                      size="small"
                      variant={selectedFormats.includes(fmt.id) ? 'filled' : 'outlined'}
                      color={selectedFormats.includes(fmt.id) ? 'primary' : 'default'}
                      onClick={() => {
                        setSelectedFormats((prev) =>
                          prev.includes(fmt.id) ? prev.filter((f) => f !== fmt.id) : [...prev, fmt.id]
                        );
                      }}
                    />
                  ))}
                </Box>

                <Divider sx={{ mb: 2 }} />

                {contentsLoading ? (
                  <Skeleton variant="rectangular" height={300} />
                ) : !contents?.length ? (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography color="text.secondary">
                      {generateMutation.isPending
                        ? 'Generating content with AI...'
                        : 'Select formats above and click "Generate More"'}
                    </Typography>
                    {generateMutation.isPending && <CircularProgress sx={{ mt: 2 }} />}
                  </Box>
                ) : (
                  <Grid container spacing={2}>
                    {contents.map((content) => {
                      const fmtInfo = FORMAT_OPTIONS.find((f) => f.id === content.format);
                      return (
                        <Grid item xs={12} sm={6} key={content.id}>
                          <Card
                            variant="outlined"
                            sx={{ cursor: 'pointer', '&:hover': { borderColor: 'primary.main' } }}
                            onClick={() => setViewContent(content)}
                          >
                            <CardContent>
                              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="subtitle2">
                                  {fmtInfo?.icon} {fmtInfo?.label || content.format}
                                </Typography>
                                <Chip
                                  label={content.status}
                                  size="small"
                                  color={STATUS_COLORS[content.status] || 'default'}
                                />
                              </Box>
                              {content.title && (
                                <Typography variant="body2" fontWeight="bold" sx={{ mb: 0.5 }}>
                                  {content.title}
                                </Typography>
                              )}
                              <Typography variant="body2" color="text.secondary" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}>
                                {content.content.substring(0, 200)}...
                              </Typography>
                              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 1 }}>
                                <Typography variant="caption" color="text.secondary">
                                  {content.word_count} words | v{content.version}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {content.provider}
                                </Typography>
                              </Box>
                            </CardContent>
                          </Card>
                        </Grid>
                      );
                    })}
                  </Grid>
                )}

                {generateMutation.isError && (
                  <Alert severity="error" sx={{ mt: 2 }}>{generateMutation.error?.message}</Alert>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <AutoAwesomeIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Select a project or create a new one
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Paste any text, select a transcription, or enter a URL to generate multi-format content
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Create Project Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>New Content Project</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Project Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            fullWidth
            multiline
            rows={8}
            label="Source Text"
            placeholder="Paste the content you want to transform (article, transcription, notes...)"
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Tone</InputLabel>
                <Select value={tone} label="Tone" onChange={(e) => setTone(e.target.value)}>
                  {TONE_OPTIONS.map((t) => (
                    <MenuItem key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                size="small"
                label="Target Audience (optional)"
                placeholder="e.g., tech professionals, students"
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
              />
            </Grid>
          </Grid>
          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>Output Formats</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {FORMAT_OPTIONS.map((fmt) => (
              <Chip
                key={fmt.id}
                label={`${fmt.icon} ${fmt.label}`}
                variant={selectedFormats.includes(fmt.id) ? 'filled' : 'outlined'}
                color={selectedFormats.includes(fmt.id) ? 'primary' : 'default'}
                onClick={() => {
                  setSelectedFormats((prev) =>
                    prev.includes(fmt.id) ? prev.filter((f) => f !== fmt.id) : [...prev, fmt.id]
                  );
                }}
              />
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!title.trim() || !sourceText.trim() || selectedFormats.length === 0 || createMutation.isPending}
            startIcon={createMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <AutoAwesomeIcon />}
          >
            Create & Generate
          </Button>
        </DialogActions>
      </Dialog>

      {/* Content Viewer Dialog */}
      <Dialog open={!!viewContent} onClose={() => setViewContent(null)} maxWidth="md" fullWidth>
        {viewContent && (
          <>
            <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="h6">
                  {FORMAT_OPTIONS.find((f) => f.id === viewContent.format)?.icon}{' '}
                  {FORMAT_OPTIONS.find((f) => f.id === viewContent.format)?.label}
                </Typography>
                {viewContent.title && (
                  <Typography variant="body2" color="text.secondary">{viewContent.title}</Typography>
                )}
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Tooltip title="Copy to clipboard">
                  <IconButton onClick={() => handleCopy(viewContent.content)} size="small">
                    <ContentCopyIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Regenerate">
                  <IconButton
                    onClick={() => {
                      regenerateMutation.mutate({ id: viewContent.id });
                      setViewContent(null);
                    }}
                    size="small"
                    disabled={regenerateMutation.isPending}
                  >
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </DialogTitle>
            <DialogContent dividers>
              <Box
                sx={{
                  whiteSpace: 'pre-wrap',
                  fontFamily: viewContent.format === 'seo_meta' ? 'monospace' : 'inherit',
                  fontSize: '0.9rem',
                  lineHeight: 1.8,
                }}
              >
                {viewContent.content}
              </Box>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  {viewContent.word_count} words
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Version {viewContent.version}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Provider: {viewContent.provider}
                </Typography>
                <Chip label={viewContent.status} size="small" color={STATUS_COLORS[viewContent.status] || 'default'} />
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setViewContent(null)}>Close</Button>
              <Button
                variant="contained"
                onClick={() => handleCopy(viewContent.content)}
                startIcon={<ContentCopyIcon />}
              >
                Copy Content
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
}
