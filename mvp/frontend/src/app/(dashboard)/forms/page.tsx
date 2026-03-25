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
  FormControl,
  FormControlLabel,
  Grid,
  IconButton,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Skeleton,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import DynamicFormIcon from '@mui/icons-material/DynamicForm';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import BarChartIcon from '@mui/icons-material/BarChart';
import ListAltIcon from '@mui/icons-material/ListAlt';
import PublishIcon from '@mui/icons-material/Publish';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import BlockIcon from '@mui/icons-material/Block';
import LinkIcon from '@mui/icons-material/Link';
import GradeIcon from '@mui/icons-material/Grade';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';

import {
  useForms,
  useCreateForm,
  useDeleteForm,
  usePublishForm,
  useCloseForm,
  useGenerateForm,
  useFormResponses,
  useFormAnalytics,
  useScoreResponse,
} from '@/features/ai-forms/hooks/useAIForms';
import type { Form, FormField } from '@/features/ai-forms/types';

const FIELD_TYPES = [
  { value: 'text', label: 'Text' },
  { value: 'email', label: 'Email' },
  { value: 'number', label: 'Number' },
  { value: 'select', label: 'Select' },
  { value: 'multiselect', label: 'Multi-Select' },
  { value: 'rating', label: 'Rating' },
  { value: 'textarea', label: 'Textarea' },
  { value: 'date', label: 'Date' },
  { value: 'file', label: 'File' },
] as const;

const STYLE_OPTIONS = ['conversational', 'classic', 'quiz', 'survey'];

const STATUS_COLORS: Record<string, 'default' | 'success' | 'error'> = {
  draft: 'default',
  published: 'success',
  closed: 'error',
};

export default function FormsPage() {
  const { data: forms, isLoading } = useForms();
  const createMutation = useCreateForm();
  const deleteMutation = useDeleteForm();
  const publishMutation = usePublishForm();
  const closeMutation = useCloseForm();
  const generateMutation = useGenerateForm();
  const scoreMutation = useScoreResponse();

  // Create dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [style, setStyle] = useState('conversational');
  const [thankYouMessage, setThankYouMessage] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [editFields, setEditFields] = useState<FormField[]>([]);

  // Generate dialog
  const [generateOpen, setGenerateOpen] = useState(false);
  const [generatePrompt, setGeneratePrompt] = useState('');
  const [generateNumFields, setGenerateNumFields] = useState(5);

  // Detail / responses dialog
  const [detailForm, setDetailForm] = useState<Form | null>(null);
  const [responsesFormId, setResponsesFormId] = useState<string | null>(null);
  const [responsesOpen, setResponsesOpen] = useState(false);

  // Analytics dialog
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [analyticsFormId, setAnalyticsFormId] = useState<string | null>(null);

  const { data: responses } = useFormResponses(responsesOpen ? responsesFormId : null);
  const { data: analytics } = useFormAnalytics(analyticsOpen ? analyticsFormId : null);

  const resetCreateForm = () => {
    setTitle('');
    setDescription('');
    setStyle('conversational');
    setThankYouMessage('');
    setIsPublic(false);
    setEditFields([]);
  };

  const handleCreate = () => {
    if (!title.trim()) return;
    createMutation.mutate(
      {
        title,
        description: description || undefined,
        fields: editFields,
        style,
        thank_you_message: thankYouMessage || undefined,
        is_public: isPublic,
      },
      {
        onSuccess: () => {
          setCreateOpen(false);
          resetCreateForm();
        },
      }
    );
  };

  const handleGenerate = () => {
    if (!generatePrompt.trim()) return;
    generateMutation.mutate(
      { prompt: generatePrompt, num_fields: generateNumFields },
      {
        onSuccess: () => {
          setGenerateOpen(false);
          setGeneratePrompt('');
          setGenerateNumFields(5);
        },
      }
    );
  };

  const handleAddField = () => {
    const newField: FormField = {
      field_id: `field_${Date.now()}`,
      type: 'text',
      label: '',
      required: false,
      options: null,
      validation: null,
      condition: null,
    };
    setEditFields([...editFields, newField]);
  };

  const handleUpdateField = (index: number, updates: Partial<FormField>) => {
    const updated = [...editFields];
    updated[index] = { ...updated[index], ...updates };
    setEditFields(updated);
  };

  const handleRemoveField = (index: number) => {
    setEditFields(editFields.filter((_, i) => i !== index));
  };

  const handleMoveField = (index: number, direction: 'up' | 'down') => {
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= editFields.length) return;
    const updated = [...editFields];
    [updated[index], updated[newIndex]] = [updated[newIndex], updated[index]];
    setEditFields(updated);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DynamicFormIcon color="primary" /> AI Forms
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create AI-powered forms with smart validation, response analysis, and AI-generated fields
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<AutoAwesomeIcon />}
            onClick={() => setGenerateOpen(true)}
          >
            AI Generate
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
            New Form
          </Button>
        </Box>
      </Box>

      {isLoading ? (
        <Grid container spacing={3}>
          {[1, 2, 3].map((i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 2 }} />
            </Grid>
          ))}
        </Grid>
      ) : !forms?.length ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <DynamicFormIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No forms yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
              Create your first AI-powered form or let AI generate one for you
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
              <Button
                variant="outlined"
                startIcon={<AutoAwesomeIcon />}
                onClick={() => setGenerateOpen(true)}
              >
                AI Generate
              </Button>
              <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
                Create Form
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {forms.map((form) => (
            <Grid item xs={12} sm={6} md={4} key={form.id}>
              <Card
                variant="outlined"
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  '&:hover': { borderColor: 'primary.main' },
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="h6" noWrap sx={{ maxWidth: '70%' }}>
                      {form.title}
                    </Typography>
                    <Chip
                      label={form.status}
                      size="small"
                      color={STATUS_COLORS[form.status] || 'default'}
                    />
                  </Box>

                  {form.description && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        mb: 1.5,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                      }}
                    >
                      {form.description}
                    </Typography>
                  )}

                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1.5 }}>
                    <Chip label={`${form.fields.length} fields`} size="small" variant="outlined" color="primary" />
                    <Chip label={form.style} size="small" variant="outlined" />
                    {form.is_public && <Chip label="Public" size="small" color="info" />}
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <ListAltIcon fontSize="small" color="action" />
                      <Typography variant="caption" color="text.secondary">
                        {form.responses_count} response{form.responses_count !== 1 ? 's' : ''}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>

                <CardActions sx={{ justifyContent: 'flex-end', pt: 0 }}>
                  {form.status === 'draft' && (
                    <Tooltip title="Publish">
                      <IconButton
                        size="small"
                        color="success"
                        onClick={() => publishMutation.mutate(form.id)}
                        disabled={publishMutation.isPending}
                      >
                        <PublishIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                  {form.status === 'published' && (
                    <Tooltip title="Close">
                      <IconButton
                        size="small"
                        color="warning"
                        onClick={() => closeMutation.mutate(form.id)}
                        disabled={closeMutation.isPending}
                      >
                        <BlockIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                  {form.share_token && (
                    <Tooltip title="Copy Share Link">
                      <IconButton
                        size="small"
                        onClick={() => handleCopy(`${window.location.origin}/forms/public/${form.share_token}`)}
                      >
                        <LinkIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                  <Tooltip title="Responses">
                    <IconButton
                      size="small"
                      onClick={() => {
                        setResponsesFormId(form.id);
                        setResponsesOpen(true);
                      }}
                    >
                      <ListAltIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Analytics">
                    <IconButton
                      size="small"
                      onClick={() => {
                        setAnalyticsFormId(form.id);
                        setAnalyticsOpen(true);
                      }}
                    >
                      <BarChartIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Details">
                    <IconButton size="small" onClick={() => setDetailForm(form)}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => deleteMutation.mutate(form.id)}
                      disabled={deleteMutation.isPending}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Form Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>New Form</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Form Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Customer Feedback Survey"
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            fullWidth
            label="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief description of the form"
            sx={{ mb: 2 }}
          />
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
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
            <Grid item xs={6}>
              <FormControlLabel
                control={<Switch checked={isPublic} onChange={(e) => setIsPublic(e.target.checked)} />}
                label="Public form"
              />
            </Grid>
          </Grid>
          <TextField
            fullWidth
            label="Thank You Message (optional)"
            value={thankYouMessage}
            onChange={(e) => setThankYouMessage(e.target.value)}
            placeholder="Message shown after submission"
            sx={{ mb: 2 }}
          />

          {/* Fields Builder */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="subtitle2">Fields</Typography>
              <Button size="small" startIcon={<AddIcon />} onClick={handleAddField}>
                Add Field
              </Button>
            </Box>

            {editFields.map((field, index) => (
              <Card key={field.field_id} variant="outlined" sx={{ mb: 1, p: 1.5 }}>
                <Grid container spacing={1} alignItems="center">
                  <Grid item xs={4}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Label"
                      value={field.label}
                      onChange={(e) => handleUpdateField(index, { label: e.target.value })}
                    />
                  </Grid>
                  <Grid item xs={2}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Type</InputLabel>
                      <Select
                        value={field.type}
                        label="Type"
                        onChange={(e) =>
                          handleUpdateField(index, {
                            type: e.target.value as FormField['type'],
                            options:
                              e.target.value === 'select' || e.target.value === 'multiselect'
                                ? field.options || []
                                : null,
                          })
                        }
                      >
                        {FIELD_TYPES.map((ft) => (
                          <MenuItem key={ft.value} value={ft.value}>
                            {ft.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={2}>
                    <FormControlLabel
                      control={
                        <Switch
                          size="small"
                          checked={field.required}
                          onChange={(e) => handleUpdateField(index, { required: e.target.checked })}
                        />
                      }
                      label="Req"
                    />
                  </Grid>
                  {(field.type === 'select' || field.type === 'multiselect') && (
                    <Grid item xs={2}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Options (comma)"
                        value={(field.options || []).join(', ')}
                        onChange={(e) =>
                          handleUpdateField(index, {
                            options: e.target.value.split(',').map((o) => o.trim()).filter(Boolean),
                          })
                        }
                      />
                    </Grid>
                  )}
                  <Grid item xs={field.type === 'select' || field.type === 'multiselect' ? 2 : 4} sx={{ textAlign: 'right' }}>
                    <IconButton
                      size="small"
                      onClick={() => handleMoveField(index, 'up')}
                      disabled={index === 0}
                    >
                      <ArrowUpwardIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleMoveField(index, 'down')}
                      disabled={index === editFields.length - 1}
                    >
                      <ArrowDownwardIcon fontSize="small" />
                    </IconButton>
                    <IconButton size="small" color="error" onClick={() => handleRemoveField(index)}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Grid>
                </Grid>
              </Card>
            ))}

            {editFields.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                No fields added yet. Click &quot;Add Field&quot; to start building.
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!title.trim() || createMutation.isPending}
            startIcon={
              createMutation.isPending ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <DynamicFormIcon />
              )
            }
          >
            Create Form
          </Button>
        </DialogActions>
      </Dialog>

      {/* AI Generate Dialog */}
      <Dialog open={generateOpen} onClose={() => setGenerateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AutoAwesomeIcon color="primary" /> AI Form Generator
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Describe the form you want and AI will generate the fields for you.
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Describe your form"
            value={generatePrompt}
            onChange={(e) => setGeneratePrompt(e.target.value)}
            placeholder="e.g., A customer satisfaction survey for an e-commerce platform with questions about delivery, product quality, and support experience"
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            type="number"
            label="Number of fields"
            value={generateNumFields}
            onChange={(e) => setGenerateNumFields(Math.max(1, Math.min(30, parseInt(e.target.value) || 5)))}
            inputProps={{ min: 1, max: 30 }}
            size="small"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGenerateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleGenerate}
            disabled={!generatePrompt.trim() || generateMutation.isPending}
            startIcon={
              generateMutation.isPending ? (
                <CircularProgress size={16} color="inherit" />
              ) : (
                <AutoAwesomeIcon />
              )
            }
          >
            Generate
          </Button>
        </DialogActions>
      </Dialog>

      {/* Form Detail Dialog */}
      <Dialog open={!!detailForm} onClose={() => setDetailForm(null)} maxWidth="md" fullWidth>
        {detailForm && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <DynamicFormIcon color="primary" />
                {detailForm.title}
                <Chip
                  label={detailForm.status}
                  size="small"
                  color={STATUS_COLORS[detailForm.status] || 'default'}
                />
              </Box>
            </DialogTitle>
            <DialogContent dividers>
              {detailForm.description && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">Description</Typography>
                  <Typography variant="body2">{detailForm.description}</Typography>
                </Box>
              )}

              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={3}>
                  <Typography variant="caption" color="text.secondary">Style</Typography>
                  <Typography variant="body2">{detailForm.style}</Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="caption" color="text.secondary">Fields</Typography>
                  <Typography variant="body2">{detailForm.fields.length}</Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="caption" color="text.secondary">Responses</Typography>
                  <Typography variant="body2">{detailForm.responses_count}</Typography>
                </Grid>
                <Grid item xs={3}>
                  <Typography variant="caption" color="text.secondary">Public</Typography>
                  <Typography variant="body2">{detailForm.is_public ? 'Yes' : 'No'}</Typography>
                </Grid>
              </Grid>

              {detailForm.share_token && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">Share Token</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography
                      variant="body2"
                      fontFamily="monospace"
                      sx={{ bgcolor: 'action.hover', px: 1, py: 0.5, borderRadius: 0.5 }}
                    >
                      {detailForm.share_token}
                    </Typography>
                    <IconButton size="small" onClick={() => handleCopy(detailForm.share_token!)}>
                      <ContentCopyIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </Box>
              )}

              {detailForm.thank_you_message && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">Thank You Message</Typography>
                  <Typography variant="body2">{detailForm.thank_you_message}</Typography>
                </Box>
              )}

              <Typography variant="subtitle2" sx={{ mb: 1 }}>Fields</Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Label</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Required</TableCell>
                      <TableCell>Options</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {detailForm.fields.map((field) => (
                      <TableRow key={field.field_id}>
                        <TableCell>{field.label}</TableCell>
                        <TableCell>
                          <Chip label={field.type} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>{field.required ? 'Yes' : 'No'}</TableCell>
                        <TableCell>
                          {field.options ? field.options.join(', ') : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailForm(null)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Responses Dialog */}
      <Dialog
        open={responsesOpen}
        onClose={() => setResponsesOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ListAltIcon color="primary" /> Form Responses
          </Box>
        </DialogTitle>
        <DialogContent>
          {responses ? (
            responses.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                No responses yet.
              </Typography>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Submitted</TableCell>
                      <TableCell>Answers</TableCell>
                      <TableCell>Score</TableCell>
                      <TableCell>Analysis</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {responses.map((resp) => (
                      <TableRow key={resp.id}>
                        <TableCell>
                          {new Date(resp.submitted_at).toLocaleString()}
                        </TableCell>
                        <TableCell sx={{ maxWidth: 300 }}>
                          <Typography
                            variant="body2"
                            noWrap
                            sx={{
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                            }}
                          >
                            {JSON.stringify(resp.answers)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {resp.score !== null ? (
                            <Chip
                              label={`${(resp.score * 100).toFixed(0)}%`}
                              size="small"
                              color={resp.score >= 0.7 ? 'success' : resp.score >= 0.4 ? 'warning' : 'error'}
                            />
                          ) : (
                            '-'
                          )}
                        </TableCell>
                        <TableCell sx={{ maxWidth: 200 }}>
                          <Typography variant="body2" noWrap>
                            {resp.analysis || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Tooltip title="AI Score">
                            <IconButton
                              size="small"
                              onClick={() =>
                                scoreMutation.mutate({
                                  formId: responsesFormId!,
                                  responseId: resp.id,
                                })
                              }
                              disabled={scoreMutation.isPending}
                            >
                              <GradeIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResponsesOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Analytics Dialog */}
      <Dialog open={analyticsOpen} onClose={() => setAnalyticsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BarChartIcon color="primary" /> Form Analytics
          </Box>
        </DialogTitle>
        <DialogContent>
          {analytics ? (
            <Box>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={4}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4">{analytics.total_responses}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        Total Responses
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={4}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4">
                        {(analytics.completion_rate * 100).toFixed(0)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Completion Rate
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={4}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4">
                        {Object.keys(analytics.field_stats).length}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Fields Tracked
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Field stats */}
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Field Statistics</Typography>
              {Object.entries(analytics.field_stats).map(([fieldId, stat]) => (
                <Box key={fieldId} sx={{ mb: 1.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2">{stat.label}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {stat.response_count} responses ({(stat.fill_rate * 100).toFixed(0)}%)
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={stat.fill_rate * 100}
                    sx={{ height: 6, borderRadius: 3 }}
                  />
                  {stat.average !== undefined && (
                    <Typography variant="caption" color="text.secondary">
                      Avg: {stat.average} | Min: {stat.min} | Max: {stat.max}
                    </Typography>
                  )}
                </Box>
              ))}

              {/* AI Insights */}
              {analytics.ai_insights && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>AI Insights</Typography>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography
                        variant="body2"
                        sx={{ whiteSpace: 'pre-wrap' }}
                      >
                        {analytics.ai_insights}
                      </Typography>
                    </CardContent>
                  </Card>
                </Box>
              )}
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAnalyticsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {createMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>{createMutation.error?.message}</Alert>
      )}
      {generateMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>{generateMutation.error?.message}</Alert>
      )}
    </Box>
  );
}
