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
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Skeleton,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CodeIcon from '@mui/icons-material/Code';
import BarChartIcon from '@mui/icons-material/BarChart';
import ChatIcon from '@mui/icons-material/Chat';
import PublicIcon from '@mui/icons-material/Public';

import {
  useChatbots,
  useCreateChatbot,
  useDeleteChatbot,
  usePublishChatbot,
  useUnpublishChatbot,
  useChatbotAnalytics,
  useEmbedCode,
} from '@/features/ai-chatbot-builder/hooks/useChatbotBuilder';
import type { Chatbot } from '@/features/ai-chatbot-builder/types';

const MODEL_OPTIONS = ['gemini', 'claude', 'groq'];
const PERSONALITY_OPTIONS = ['professional', 'friendly', 'casual', 'technical', 'empathetic', 'concise'];

export default function ChatbotsPage() {
  const { data: chatbots, isLoading } = useChatbots();
  const createMutation = useCreateChatbot();
  const deleteMutation = useDeleteChatbot();
  const publishMutation = usePublishChatbot();
  const unpublishMutation = useUnpublishChatbot();

  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful assistant.');
  const [model, setModel] = useState('gemini');
  const [personality, setPersonality] = useState('professional');
  const [welcomeMessage, setWelcomeMessage] = useState('');

  const [detailBot, setDetailBot] = useState<Chatbot | null>(null);
  const [embedOpen, setEmbedOpen] = useState(false);
  const [embedBotId, setEmbedBotId] = useState<string | null>(null);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [analyticsBotId, setAnalyticsBotId] = useState<string | null>(null);

  const { data: embedCode } = useEmbedCode(embedOpen ? embedBotId : null);
  const { data: analytics } = useChatbotAnalytics(analyticsOpen ? analyticsBotId : null);

  const handleCreate = () => {
    if (!name.trim() || !systemPrompt.trim()) return;
    createMutation.mutate(
      {
        name,
        description: description || undefined,
        system_prompt: systemPrompt,
        model,
        personality,
        welcome_message: welcomeMessage || undefined,
      },
      {
        onSuccess: () => {
          setCreateOpen(false);
          setName('');
          setDescription('');
          setSystemPrompt('You are a helpful assistant.');
          setModel('gemini');
          setPersonality('professional');
          setWelcomeMessage('');
        },
      }
    );
  };

  const handleTogglePublish = (bot: Chatbot) => {
    if (bot.is_published) {
      unpublishMutation.mutate(bot.id);
    } else {
      publishMutation.mutate(bot.id);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SmartToyIcon color="primary" /> Chatbot Builder
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create AI chatbots with custom knowledge bases, deploy on web widgets and messaging channels
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
          New Chatbot
        </Button>
      </Box>

      {isLoading ? (
        <Grid container spacing={3}>
          {[1, 2, 3].map((i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rectangular" height={220} sx={{ borderRadius: 2 }} />
            </Grid>
          ))}
        </Grid>
      ) : !chatbots?.length ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <SmartToyIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No chatbots yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
              Build your first AI chatbot with custom instructions, knowledge base integration, and multi-channel deployment
            </Typography>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
              Create your first chatbot
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {chatbots.map((bot) => (
            <Grid item xs={12} sm={6} md={4} key={bot.id}>
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
                      {bot.name}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Tooltip title={bot.is_published ? 'Published' : 'Draft'}>
                        <Switch
                          size="small"
                          checked={bot.is_published}
                          onChange={() => handleTogglePublish(bot)}
                          disabled={publishMutation.isPending || unpublishMutation.isPending}
                        />
                      </Tooltip>
                    </Box>
                  </Box>

                  {bot.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5, overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                      {bot.description}
                    </Typography>
                  )}

                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1.5 }}>
                    <Chip label={bot.model} size="small" variant="outlined" color="primary" />
                    <Chip label={bot.personality} size="small" variant="outlined" />
                    {bot.is_published && (
                      <Chip label="Published" size="small" color="success" icon={<PublicIcon />} />
                    )}
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <ChatIcon fontSize="small" color="action" />
                      <Typography variant="caption" color="text.secondary">
                        {bot.conversations_count} conversations
                      </Typography>
                    </Box>
                    {bot.channels.length > 0 && (
                      <Typography variant="caption" color="text.secondary">
                        {bot.channels.length} channel{bot.channels.length > 1 ? 's' : ''}
                      </Typography>
                    )}
                  </Box>
                </CardContent>

                <CardActions sx={{ justifyContent: 'flex-end', pt: 0 }}>
                  <Tooltip title="Analytics">
                    <IconButton
                      size="small"
                      onClick={() => {
                        setAnalyticsBotId(bot.id);
                        setAnalyticsOpen(true);
                      }}
                    >
                      <BarChartIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  {bot.is_published && (
                    <Tooltip title="Embed Code">
                      <IconButton
                        size="small"
                        onClick={() => {
                          setEmbedBotId(bot.id);
                          setEmbedOpen(true);
                        }}
                      >
                        <CodeIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                  <Tooltip title="Edit">
                    <IconButton size="small" onClick={() => setDetailBot(bot)}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => deleteMutation.mutate(bot.id)}
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

      {/* Create Chatbot Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>New Chatbot</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Chatbot Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Customer Support Bot"
            sx={{ mt: 1, mb: 2 }}
          />
          <TextField
            fullWidth
            label="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief description of what this chatbot does"
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            multiline
            rows={5}
            label="System Prompt"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            placeholder="Instructions for the AI. Define its role, knowledge boundaries, and response style."
            sx={{ mb: 2 }}
          />
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <FormControl fullWidth size="small">
                <InputLabel>AI Model</InputLabel>
                <Select value={model} label="AI Model" onChange={(e) => setModel(e.target.value)}>
                  {MODEL_OPTIONS.map((m) => (
                    <MenuItem key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Personality</InputLabel>
                <Select value={personality} label="Personality" onChange={(e) => setPersonality(e.target.value)}>
                  {PERSONALITY_OPTIONS.map((p) => (
                    <MenuItem key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
          <TextField
            fullWidth
            label="Welcome Message (optional)"
            value={welcomeMessage}
            onChange={(e) => setWelcomeMessage(e.target.value)}
            placeholder="First message shown to users, e.g., Hello! How can I help you today?"
            sx={{ mb: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!name.trim() || !systemPrompt.trim() || createMutation.isPending}
            startIcon={createMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <SmartToyIcon />}
          >
            Create Chatbot
          </Button>
        </DialogActions>
      </Dialog>

      {/* Chatbot Detail / Edit Dialog */}
      <Dialog open={!!detailBot} onClose={() => setDetailBot(null)} maxWidth="md" fullWidth>
        {detailBot && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SmartToyIcon color="primary" />
                {detailBot.name}
                {detailBot.is_published && <Chip label="Published" size="small" color="success" />}
              </Box>
            </DialogTitle>
            <DialogContent dividers>
              <Typography variant="subtitle2" sx={{ mb: 0.5 }}>System Prompt</Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', bgcolor: 'action.hover', p: 1.5, borderRadius: 1, mb: 2 }}>
                {detailBot.system_prompt}
              </Typography>

              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={4}>
                  <Typography variant="caption" color="text.secondary">Model</Typography>
                  <Typography variant="body2">{detailBot.model}</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="caption" color="text.secondary">Personality</Typography>
                  <Typography variant="body2">{detailBot.personality}</Typography>
                </Grid>
                <Grid item xs={4}>
                  <Typography variant="caption" color="text.secondary">Conversations</Typography>
                  <Typography variant="body2">{detailBot.conversations_count}</Typography>
                </Grid>
              </Grid>

              {detailBot.welcome_message && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">Welcome Message</Typography>
                  <Typography variant="body2">{detailBot.welcome_message}</Typography>
                </Box>
              )}

              {detailBot.embed_token && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary">Embed Token</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" fontFamily="monospace" sx={{ bgcolor: 'action.hover', px: 1, py: 0.5, borderRadius: 0.5 }}>
                      {detailBot.embed_token}
                    </Typography>
                    <IconButton size="small" onClick={() => handleCopy(detailBot.embed_token!)}>
                      <ContentCopyIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </Box>
              )}

              {detailBot.channels.length > 0 && (
                <Box>
                  <Typography variant="caption" color="text.secondary">Channels</Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                    {detailBot.channels.map((ch, i) => (
                      <Chip key={i} label={ch.type} size="small" variant="outlined" color={ch.is_active ? 'success' : 'default'} />
                    ))}
                  </Box>
                </Box>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailBot(null)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Embed Code Dialog */}
      <Dialog open={embedOpen} onClose={() => setEmbedOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CodeIcon color="primary" /> Embed Code
          </Box>
        </DialogTitle>
        <DialogContent>
          {embedCode ? (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Add this snippet to your website to embed the chatbot widget:
              </Typography>
              <Box
                sx={{
                  fontFamily: 'monospace',
                  fontSize: '0.85rem',
                  bgcolor: 'grey.900',
                  color: 'grey.100',
                  p: 2,
                  borderRadius: 1,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                }}
              >
                {embedCode.html_snippet}
              </Box>
              <Button
                startIcon={<ContentCopyIcon />}
                onClick={() => handleCopy(embedCode.html_snippet)}
                sx={{ mt: 1 }}
              >
                Copy Snippet
              </Button>
            </Box>
          ) : (
            <CircularProgress />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEmbedOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Analytics Dialog */}
      <Dialog open={analyticsOpen} onClose={() => setAnalyticsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BarChartIcon color="primary" /> Chatbot Analytics
          </Box>
        </DialogTitle>
        <DialogContent>
          {analytics ? (
            <Box>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4">{analytics.total_conversations}</Typography>
                      <Typography variant="caption" color="text.secondary">Conversations</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4">{analytics.total_messages}</Typography>
                      <Typography variant="caption" color="text.secondary">Messages</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4">{analytics.avg_messages_per_conversation}</Typography>
                      <Typography variant="caption" color="text.secondary">Avg Messages/Conv</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h4">
                        {analytics.satisfaction_score !== null ? analytics.satisfaction_score : '--'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">Satisfaction</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {analytics.top_questions.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>Top Questions</Typography>
                  {analytics.top_questions.map((q, i) => (
                    <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                      <Typography variant="body2" noWrap sx={{ maxWidth: '80%' }}>{q.question}</Typography>
                      <Chip label={q.count} size="small" />
                    </Box>
                  ))}
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
    </Box>
  );
}
