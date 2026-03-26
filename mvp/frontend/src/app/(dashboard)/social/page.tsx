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
  Tab,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SendIcon from '@mui/icons-material/Send';
import ScheduleIcon from '@mui/icons-material/Schedule';
import BarChartIcon from '@mui/icons-material/BarChart';
import LinkOffIcon from '@mui/icons-material/LinkOff';
import ShareIcon from '@mui/icons-material/Share';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

import {
  useAccounts,
  useConnectAccount,
  useCreatePost,
  useDeletePost,
  useDisconnectAccount,
  usePostAnalytics,
  usePosts,
  usePublishPost,
} from '@/features/social-publisher/hooks/useSocialPublisher';
import type { SocialPost } from '@/features/social-publisher/types';

const PLATFORM_OPTIONS = [
  { id: 'twitter', label: 'Twitter / X', color: '#1DA1F2' },
  { id: 'linkedin', label: 'LinkedIn', color: '#0077B5' },
  { id: 'instagram', label: 'Instagram', color: '#E4405F' },
  { id: 'tiktok', label: 'TikTok', color: '#000000' },
  { id: 'facebook', label: 'Facebook', color: '#1877F2' },
];

const STATUS_COLORS: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning' | 'info'> = {
  draft: 'default',
  scheduled: 'warning',
  publishing: 'info',
  published: 'success',
  failed: 'error',
};

type TabValue = 'compose' | 'scheduled' | 'published' | 'accounts';

export default function SocialPublisherPage() {
  const [activeTab, setActiveTab] = useState<TabValue>('compose');

  // Data hooks
  const { data: accounts, isLoading: accountsLoading } = useAccounts();
  const { data: postsData, isLoading: postsLoading } = usePosts({ limit: 50 });
  const connectMutation = useConnectAccount();
  const disconnectMutation = useDisconnectAccount();
  const createPostMutation = useCreatePost();
  const publishMutation = usePublishPost();
  const deleteMutation = useDeletePost();

  // Compose state
  const [content, setContent] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(['twitter', 'linkedin']);
  const [hashtags, setHashtags] = useState('');
  const [scheduleDate, setScheduleDate] = useState('');

  // Connect account dialog
  const [connectOpen, setConnectOpen] = useState(false);
  const [connectPlatform, setConnectPlatform] = useState('twitter');
  const [connectToken, setConnectToken] = useState('');
  const [connectName, setConnectName] = useState('');

  // Analytics dialog
  const [analyticsPostId, setAnalyticsPostId] = useState<string | null>(null);
  const { data: analytics } = usePostAnalytics(analyticsPostId);

  const posts = postsData?.posts || [];
  const draftPosts = posts.filter((p) => p.status === 'draft');
  const scheduledPosts = posts.filter((p) => p.status === 'scheduled');
  const publishedPosts = posts.filter((p) => p.status === 'published' || p.status === 'failed');

  const handleCompose = () => {
    if (!content.trim() || selectedPlatforms.length === 0) return;
    const hashtagList = hashtags
      .split(/[,\s]+/)
      .map((h) => h.trim())
      .filter(Boolean);

    createPostMutation.mutate(
      {
        content,
        platforms: selectedPlatforms,
        schedule_at: scheduleDate || undefined,
        hashtags: hashtagList.length > 0 ? hashtagList : undefined,
      },
      {
        onSuccess: () => {
          setContent('');
          setHashtags('');
          setScheduleDate('');
        },
      }
    );
  };

  const handleConnect = () => {
    if (!connectToken.trim() || !connectName.trim()) return;
    connectMutation.mutate(
      {
        platform: connectPlatform as 'twitter' | 'linkedin' | 'instagram' | 'tiktok' | 'facebook',
        access_token: connectToken,
        account_name: connectName,
      },
      {
        onSuccess: () => {
          setConnectOpen(false);
          setConnectToken('');
          setConnectName('');
        },
      }
    );
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const togglePlatform = (id: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const renderPostCard = (post: SocialPost, showActions: boolean = true) => {
    const platformChips = post.platforms.map((p) => {
      const info = PLATFORM_OPTIONS.find((o) => o.id === p);
      return (
        <Chip
          key={p}
          label={info?.label || p}
          size="small"
          sx={{ bgcolor: info?.color, color: '#fff', fontSize: '0.7rem' }}
        />
      );
    });

    return (
      <Card key={post.id} variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              {platformChips}
            </Box>
            <Chip
              label={post.status}
              size="small"
              color={STATUS_COLORS[post.status] || 'default'}
            />
          </Box>
          <Typography
            variant="body2"
            sx={{
              whiteSpace: 'pre-wrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 4,
              WebkitBoxOrient: 'vertical',
              mb: 1,
            }}
          >
            {post.content}
          </Typography>
          {post.hashtags.length > 0 && (
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
              {post.hashtags.map((h) => (
                <Chip key={h} label={`#${h}`} size="small" variant="outlined" color="primary" />
              ))}
            </Box>
          )}
          <Typography variant="caption" color="text.secondary">
            {post.schedule_at
              ? `Scheduled: ${new Date(post.schedule_at).toLocaleString()}`
              : post.published_at
              ? `Published: ${new Date(post.published_at).toLocaleString()}`
              : `Created: ${new Date(post.created_at).toLocaleString()}`}
          </Typography>
        </CardContent>
        {showActions && (
          <CardActions sx={{ justifyContent: 'flex-end', pt: 0 }}>
            <Tooltip title="Copy content">
              <IconButton size="small" onClick={() => handleCopy(post.content)}>
                <ContentCopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            {(post.status === 'draft' || post.status === 'scheduled') && (
              <Tooltip title="Publish now">
                <IconButton
                  size="small"
                  color="primary"
                  onClick={() => publishMutation.mutate(post.id)}
                  disabled={publishMutation.isPending}
                >
                  <SendIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {post.status === 'published' && (
              <Tooltip title="View analytics">
                <IconButton
                  size="small"
                  color="info"
                  onClick={() => setAnalyticsPostId(post.id)}
                >
                  <BarChartIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {post.status !== 'published' && (
              <Tooltip title="Delete">
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => deleteMutation.mutate(post.id)}
                  disabled={deleteMutation.isPending}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </CardActions>
        )}
      </Card>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ShareIcon color="primary" /> Social Publisher
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Compose, schedule, and publish to multiple social media platforms
          </Typography>
        </Box>
      </Box>

      <Tabs
        value={activeTab}
        onChange={(_, v) => setActiveTab(v)}
        sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab label="Compose" value="compose" />
        <Tab label={`Scheduled (${scheduledPosts.length})`} value="scheduled" />
        <Tab label={`Published (${publishedPosts.length})`} value="published" />
        <Tab label={`Accounts (${accounts?.length || 0})`} value="accounts" />
      </Tabs>

      {/* ---- Compose Tab ---- */}
      {activeTab === 'compose' && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>New Post</Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  label="What do you want to share?"
                  placeholder="Write your post content here..."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  sx={{ mb: 2 }}
                  inputProps={{ maxLength: 10000 }}
                  helperText={`${content.length} / 10,000 characters`}
                />

                <Typography variant="subtitle2" sx={{ mb: 1 }}>Target Platforms</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                  {PLATFORM_OPTIONS.map((p) => (
                    <Chip
                      key={p.id}
                      label={p.label}
                      variant={selectedPlatforms.includes(p.id) ? 'filled' : 'outlined'}
                      sx={
                        selectedPlatforms.includes(p.id)
                          ? { bgcolor: p.color, color: '#fff' }
                          : {}
                      }
                      onClick={() => togglePlatform(p.id)}
                    />
                  ))}
                </Box>

                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Hashtags (comma separated)"
                      placeholder="AI, SaaS, innovation"
                      value={hashtags}
                      onChange={(e) => setHashtags(e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      size="small"
                      type="datetime-local"
                      label="Schedule (optional)"
                      value={scheduleDate}
                      onChange={(e) => setScheduleDate(e.target.value)}
                      InputLabelProps={{ shrink: true }}
                    />
                  </Grid>
                </Grid>

                <Box sx={{ display: 'flex', gap: 1, mt: 3, justifyContent: 'flex-end' }}>
                  <Button
                    variant="outlined"
                    startIcon={<ScheduleIcon />}
                    onClick={() => {
                      if (!scheduleDate) return;
                      handleCompose();
                    }}
                    disabled={!content.trim() || selectedPlatforms.length === 0 || !scheduleDate || createPostMutation.isPending}
                  >
                    Schedule
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={createPostMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <SendIcon />}
                    onClick={handleCompose}
                    disabled={!content.trim() || selectedPlatforms.length === 0 || createPostMutation.isPending}
                  >
                    {scheduleDate ? 'Schedule Post' : 'Create Draft'}
                  </Button>
                </Box>

                {createPostMutation.isError && (
                  <Alert severity="error" sx={{ mt: 2 }}>{createPostMutation.error?.message}</Alert>
                )}
                {createPostMutation.isSuccess && (
                  <Alert severity="success" sx={{ mt: 2 }}>Post created successfully!</Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Draft Posts sidebar */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>Drafts ({draftPosts.length})</Typography>
                {postsLoading ? (
                  <Skeleton variant="rectangular" height={200} />
                ) : draftPosts.length === 0 ? (
                  <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                    No draft posts yet
                  </Typography>
                ) : (
                  draftPosts.map((post) => renderPostCard(post))
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* ---- Scheduled Tab ---- */}
      {activeTab === 'scheduled' && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Scheduled Posts</Typography>
            {postsLoading ? (
              <Skeleton variant="rectangular" height={300} />
            ) : scheduledPosts.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 6 }}>
                <ScheduleIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography color="text.secondary">No scheduled posts</Typography>
                <Typography variant="body2" color="text.secondary">
                  Schedule posts from the Compose tab
                </Typography>
              </Box>
            ) : (
              <Grid container spacing={2}>
                {scheduledPosts.map((post) => (
                  <Grid item xs={12} sm={6} md={4} key={post.id}>
                    {renderPostCard(post)}
                  </Grid>
                ))}
              </Grid>
            )}
          </CardContent>
        </Card>
      )}

      {/* ---- Published Tab ---- */}
      {activeTab === 'published' && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Published Posts</Typography>
            {postsLoading ? (
              <Skeleton variant="rectangular" height={300} />
            ) : publishedPosts.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 6 }}>
                <ShareIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography color="text.secondary">No published posts yet</Typography>
              </Box>
            ) : (
              <Grid container spacing={2}>
                {publishedPosts.map((post) => (
                  <Grid item xs={12} sm={6} md={4} key={post.id}>
                    {renderPostCard(post)}
                  </Grid>
                ))}
              </Grid>
            )}
          </CardContent>
        </Card>
      )}

      {/* ---- Accounts Tab ---- */}
      {activeTab === 'accounts' && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">Connected Accounts</Typography>
              <Button
                variant="contained"
                size="small"
                startIcon={<AddIcon />}
                onClick={() => setConnectOpen(true)}
              >
                Connect Account
              </Button>
            </Box>
            {accountsLoading ? (
              <Skeleton variant="rectangular" height={200} />
            ) : !accounts?.length ? (
              <Box sx={{ textAlign: 'center', py: 6 }}>
                <LinkOffIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography color="text.secondary">No accounts connected</Typography>
                <Button size="small" onClick={() => setConnectOpen(true)} sx={{ mt: 1 }}>
                  Connect your first account
                </Button>
              </Box>
            ) : (
              <Grid container spacing={2}>
                {accounts.map((account) => {
                  const platformInfo = PLATFORM_OPTIONS.find((p) => p.id === account.platform);
                  return (
                    <Grid item xs={12} sm={6} md={4} key={account.id}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <Box>
                              <Chip
                                label={platformInfo?.label || account.platform}
                                size="small"
                                sx={{ bgcolor: platformInfo?.color, color: '#fff', mb: 1 }}
                              />
                              <Typography variant="subtitle1">{account.account_name}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                Connected {new Date(account.created_at).toLocaleDateString()}
                              </Typography>
                            </Box>
                            <Chip
                              label={account.is_active ? 'Active' : 'Inactive'}
                              size="small"
                              color={account.is_active ? 'success' : 'default'}
                            />
                          </Box>
                        </CardContent>
                        <CardActions sx={{ justifyContent: 'flex-end' }}>
                          {account.is_active && (
                            <Button
                              size="small"
                              color="error"
                              startIcon={<LinkOffIcon />}
                              onClick={() => disconnectMutation.mutate(account.id)}
                              disabled={disconnectMutation.isPending}
                            >
                              Disconnect
                            </Button>
                          )}
                        </CardActions>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            )}
          </CardContent>
        </Card>
      )}

      {/* ---- Connect Account Dialog ---- */}
      <Dialog open={connectOpen} onClose={() => setConnectOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Connect Social Account</DialogTitle>
        <DialogContent>
          <FormControl fullWidth size="small" sx={{ mt: 1, mb: 2 }}>
            <InputLabel>Platform</InputLabel>
            <Select
              value={connectPlatform}
              label="Platform"
              onChange={(e) => setConnectPlatform(e.target.value)}
            >
              {PLATFORM_OPTIONS.map((p) => (
                <MenuItem key={p.id} value={p.id}>{p.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            fullWidth
            size="small"
            label="Account Name / Handle"
            placeholder="@myaccount"
            value={connectName}
            onChange={(e) => setConnectName(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            size="small"
            type="password"
            label="Access Token"
            placeholder="OAuth access token"
            value={connectToken}
            onChange={(e) => setConnectToken(e.target.value)}
            helperText="Your token is hashed before storage and never displayed again"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConnectOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleConnect}
            disabled={!connectName.trim() || !connectToken.trim() || connectMutation.isPending}
            startIcon={connectMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <AddIcon />}
          >
            Connect
          </Button>
        </DialogActions>
      </Dialog>

      {/* ---- Analytics Dialog ---- */}
      <Dialog
        open={!!analyticsPostId}
        onClose={() => setAnalyticsPostId(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Post Analytics</DialogTitle>
        <DialogContent>
          {!analytics ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            analytics.map((a) => {
              const platformInfo = PLATFORM_OPTIONS.find((p) => p.id === a.platform);
              return (
                <Card key={a.platform} variant="outlined" sx={{ mb: 2 }}>
                  <CardContent>
                    <Chip
                      label={platformInfo?.label || a.platform}
                      size="small"
                      sx={{ bgcolor: platformInfo?.color, color: '#fff', mb: 1.5 }}
                    />
                    <Grid container spacing={2}>
                      <Grid item xs={3}>
                        <Typography variant="h6" align="center">{a.impressions.toLocaleString()}</Typography>
                        <Typography variant="caption" color="text.secondary" display="block" align="center">
                          Impressions
                        </Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="h6" align="center">{a.engagements.toLocaleString()}</Typography>
                        <Typography variant="caption" color="text.secondary" display="block" align="center">
                          Engagements
                        </Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="h6" align="center">{a.clicks.toLocaleString()}</Typography>
                        <Typography variant="caption" color="text.secondary" display="block" align="center">
                          Clicks
                        </Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="h6" align="center">{a.shares.toLocaleString()}</Typography>
                        <Typography variant="caption" color="text.secondary" display="block" align="center">
                          Shares
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              );
            })
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAnalyticsPostId(null)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Global mutation error/success feedback */}
      {publishMutation.isError && (
        <Alert severity="error" sx={{ position: 'fixed', bottom: 16, right: 16, zIndex: 9999 }}>
          Publish failed: {publishMutation.error?.message}
        </Alert>
      )}
      {publishMutation.isSuccess && (
        <Alert severity="success" sx={{ position: 'fixed', bottom: 16, right: 16, zIndex: 9999 }}>
          Post published successfully!
        </Alert>
      )}
    </Box>
  );
}
