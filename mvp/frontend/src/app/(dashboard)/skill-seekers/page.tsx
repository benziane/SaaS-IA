'use client';

import { useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, CardActions, Checkbox, Chip, CircularProgress,
  Divider, Drawer, FormControlLabel, Grid, IconButton, LinearProgress, Skeleton,
  Stack, Switch, TextField, Tooltip, Typography,
} from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CancelIcon from '@mui/icons-material/Cancel';
import CloseIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/Delete';
import DownloadIcon from '@mui/icons-material/Download';
import PreviewIcon from '@mui/icons-material/Visibility';
import ReplayIcon from '@mui/icons-material/Replay';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import TerminalIcon from '@mui/icons-material/Terminal';
import RefreshIcon from '@mui/icons-material/Refresh';

import { useSkillSeekersJobs, useSkillSeekersStatus, useSkillSeekersStats } from '@/features/skill-seekers/hooks/useSkillSeekers';
import { useCreateScrapeJob, useDeleteScrapeJob, useRetryScrapeJob, useCancelScrapeJob } from '@/features/skill-seekers/hooks/useSkillSeekersMutations';
import { getSignedDownloadUrl, previewFile } from '@/features/skill-seekers/api';
import { ScrapeJobStatus } from '@/features/skill-seekers/types';
import {
  CATALOGUE_REPOS,
  CATEGORY_LABELS,
  CATEGORY_COLORS,
  ALL_CATEGORIES,
  type CatalogueCategory,
} from '@/features/skill-seekers/catalogue';

function formatStars(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return String(n);
}

function SkillCatalogueDrawer({
  open,
  onClose,
  selectedRepos,
  onToggle,
  filter,
  onFilterChange,
}: {
  open: boolean;
  onClose: () => void;
  selectedRepos: string[];
  onToggle: (repo: string) => void;
  filter: CatalogueCategory | 'all';
  onFilterChange: (f: CatalogueCategory | 'all') => void;
}) {
  const filtered = filter === 'all'
    ? CATALOGUE_REPOS
    : CATALOGUE_REPOS.filter((r) => r.category === filter);

  const pendingCount = CATALOGUE_REPOS.filter(
    (r) => selectedRepos.includes(r.repo)
  ).length;

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{ sx: { width: { xs: '100%', sm: 560, md: 720 }, display: 'flex', flexDirection: 'column' } }}
    >
      {/* Header */}
      <Box sx={{ px: 3, py: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AutoAwesomeIcon color="primary" fontSize="small" />
          Catalogue Claude Skills
        </Typography>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </Box>

      {/* Filters */}
      <Box sx={{ px: 3, py: 1.5, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
          <Chip
            label="Tous"
            size="small"
            variant={filter === 'all' ? 'filled' : 'outlined'}
            color={filter === 'all' ? 'primary' : 'default'}
            onClick={() => onFilterChange('all')}
            clickable
          />
          {ALL_CATEGORIES.map((cat) => (
            <Chip
              key={cat}
              label={CATEGORY_LABELS[cat]}
              size="small"
              variant={filter === cat ? 'filled' : 'outlined'}
              onClick={() => onFilterChange(cat)}
              clickable
              sx={filter === cat ? { bgcolor: CATEGORY_COLORS[cat], color: '#fff', borderColor: CATEGORY_COLORS[cat], '&:hover': { bgcolor: CATEGORY_COLORS[cat] } } : { borderColor: CATEGORY_COLORS[cat], color: CATEGORY_COLORS[cat] }}
            />
          ))}
        </Stack>
      </Box>

      {/* Cards grid */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <Grid container spacing={1.5}>
          {filtered.map((item) => {
            const isSelected = selectedRepos.includes(item.repo);
            const isDisabled = !isSelected && selectedRepos.length >= 10;
            return (
              <Grid item xs={12} sm={6} md={4} key={item.repo}>
                <Card
                  variant="outlined"
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    opacity: isDisabled ? 0.5 : 1,
                    borderColor: isSelected ? CATEGORY_COLORS[item.category] : undefined,
                    borderWidth: isSelected ? 2 : 1,
                  }}
                >
                  <CardContent sx={{ flex: 1, pb: 0.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 0.5 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                        {item.name}
                      </Typography>
                      <Chip
                        label={CATEGORY_LABELS[item.category]}
                        size="small"
                        sx={{ ml: 0.5, fontSize: '0.65rem', height: 18, bgcolor: CATEGORY_COLORS[item.category], color: '#fff', flexShrink: 0 }}
                      />
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                      {item.repo}
                    </Typography>
                    <Typography variant="body2" sx={{ fontSize: '0.75rem', mb: 1, color: 'text.secondary' }}>
                      {item.description}
                    </Typography>
                    <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap sx={{ mb: 0.5 }}>
                      {item.tags.map((tag) => (
                        <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ fontSize: '0.6rem', height: 16 }} />
                      ))}
                    </Stack>
                    <Typography variant="caption" color="text.secondary">
                      {formatStars(item.stars)} ⭐
                    </Typography>
                  </CardContent>
                  <CardActions sx={{ pt: 0.5, pb: 1, px: 2 }}>
                    {isSelected ? (
                      <Button
                        size="small"
                        variant="outlined"
                        color="success"
                        fullWidth
                        startIcon={<Checkbox checked size="small" sx={{ p: 0 }} />}
                        onClick={() => onToggle(item.repo)}
                        sx={{ fontSize: '0.7rem' }}
                      >
                        Déjà ajouté
                      </Button>
                    ) : (
                      <Button
                        size="small"
                        variant="contained"
                        fullWidth
                        disabled={isDisabled}
                        onClick={() => onToggle(item.repo)}
                        sx={{ fontSize: '0.7rem' }}
                      >
                        Ajouter
                      </Button>
                    )}
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      </Box>

      {/* Footer */}
      <Box sx={{ px: 3, py: 2, borderTop: 1, borderColor: 'divider', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="body2" color="text.secondary">
          {pendingCount > 0 ? `${pendingCount} repo${pendingCount > 1 ? 's' : ''} sélectionné${pendingCount > 1 ? 's' : ''}` : 'Aucun repo sélectionné'}
        </Typography>
        <Button
          variant="contained"
          onClick={onClose}
          disabled={pendingCount === 0}
          startIcon={<RocketLaunchIcon />}
        >
          Confirmer
        </Button>
      </Box>
    </Drawer>
  );
}

const STATUS_TABS = [
  { label: 'All', value: '' },
  { label: 'Pending', value: 'pending' },
  { label: 'Running', value: 'running' },
  { label: 'Completed', value: 'completed' },
  { label: 'Failed', value: 'failed' },
];

const TARGET_OPTIONS = [
  { id: 'claude', label: 'Claude' },
  { id: 'openai', label: 'OpenAI' },
  { id: 'gemini', label: 'Gemini' },
  { id: 'langchain', label: 'LangChain' },
  { id: 'llama-index', label: 'LlamaIndex' },
  { id: 'markdown', label: 'Markdown' },
];

const STATUS_COLORS: Record<string, 'default' | 'info' | 'success' | 'error' | 'warning'> = {
  pending: 'default',
  running: 'info',
  completed: 'success',
  failed: 'error',
};

export default function SkillSeekersPage() {
  const [statusFilter, setStatusFilter] = useState('');
  const { data: statusData, isLoading: statusLoading } = useSkillSeekersStatus();
  const { data: jobsData, isLoading: jobsLoading, refetch } = useSkillSeekersJobs(0, 20, statusFilter || undefined);
  const { data: statsData } = useSkillSeekersStats();
  const createMutation = useCreateScrapeJob();
  const deleteMutation = useDeleteScrapeJob();
  const retryMutation = useRetryScrapeJob();
  const cancelMutation = useCancelScrapeJob();
  const [previewData, setPreviewData] = useState<{ filename: string; content: string } | null>(null);

  // Form state
  const [repoInput, setRepoInput] = useState('');
  const [repos, setRepos] = useState<string[]>([]);
  const [targets, setTargets] = useState<string[]>(['claude']);
  const [enhance, setEnhance] = useState(false);

  // Catalogue state
  const [catalogueOpen, setCatalogueOpen] = useState(false);
  const [catalogueFilter, setCatalogueFilter] = useState<CatalogueCategory | 'all'>('all');

  const handleAddRepo = () => {
    const trimmed = repoInput.trim();
    if (!trimmed) return;
    if (!/^[a-zA-Z0-9_\-\.]+\/[a-zA-Z0-9_\-\.]+$/.test(trimmed)) return;
    if (repos.includes(trimmed)) return;
    if (repos.length >= 10) return;
    setRepos((prev) => [...prev, trimmed]);
    setRepoInput('');
  };

  const handleRemoveRepo = (repo: string) => {
    setRepos((prev) => prev.filter((r) => r !== repo));
  };

  const handleToggleTarget = (target: string) => {
    setTargets((prev) =>
      prev.includes(target) ? prev.filter((t) => t !== target) : [...prev, target]
    );
  };

  const handleLaunch = () => {
    if (repos.length === 0 || targets.length === 0) return;
    createMutation.mutate(
      { repos, targets, enhance },
      {
        onSuccess: () => {
          setRepos([]);
          setRepoInput('');
        },
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddRepo();
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TerminalIcon color="primary" /> Skill Seekers
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Scrape GitHub repos and package them for Claude AI consumption
          </Typography>
        </Box>
        <Tooltip title="Refresh jobs">
          <IconButton onClick={() => refetch()}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* CLI status alert */}
      {!statusLoading && statusData && !statusData.installed && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <strong>skill-seekers CLI not installed.</strong> Running in mock mode.
          Install it with: <code>pip install skill-seekers</code>
        </Alert>
      )}

      {/* Stats cards */}
      {statsData && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[
            { label: 'Total Jobs', value: statsData.total_jobs, color: 'primary.main' },
            { label: 'Completed', value: statsData.completed, color: 'success.main' },
            { label: 'Failed', value: statsData.failed, color: 'error.main' },
            { label: 'Repos Scraped', value: statsData.total_repos_scraped, color: 'info.main' },
          ].map((stat) => (
            <Grid item xs={6} sm={3} key={stat.label}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 2, '&:last-child': { pb: 2 } }}>
                  <Typography variant="h4" sx={{ color: stat.color, fontWeight: 700 }}>
                    {stat.value}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {stat.label}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Grid container spacing={3}>
        {/* Left panel: Create job form */}
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <GitHubIcon /> New Scrape Job
              </Typography>

              {/* Repo input */}
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField
                  fullWidth
                  size="small"
                  label="GitHub repo (owner/repo)"
                  placeholder="e.g. anthropics/claude-code"
                  value={repoInput}
                  onChange={(e) => setRepoInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  helperText={repos.length >= 10 ? 'Max 10 repos' : undefined}
                  error={repos.length >= 10}
                />
                <Button
                  variant="outlined"
                  onClick={handleAddRepo}
                  disabled={!repoInput.trim() || repos.length >= 10}
                  sx={{ minWidth: 'auto', px: 1 }}
                >
                  <AddCircleOutlineIcon />
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<AutoAwesomeIcon />}
                  onClick={() => setCatalogueOpen(true)}
                  size="small"
                  sx={{ whiteSpace: 'nowrap' }}
                >
                  Catalogue
                </Button>
              </Box>

              {/* Repo chips */}
              {repos.length > 0 && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                  {repos.map((repo) => (
                    <Chip
                      key={repo}
                      label={repo}
                      onDelete={() => handleRemoveRepo(repo)}
                      size="small"
                      icon={<GitHubIcon />}
                    />
                  ))}
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              {/* Target checkboxes */}
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Package Targets
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0 }}>
                {TARGET_OPTIONS.map((opt) => (
                  <FormControlLabel
                    key={opt.id}
                    control={
                      <Checkbox
                        checked={targets.includes(opt.id)}
                        onChange={() => handleToggleTarget(opt.id)}
                        size="small"
                      />
                    }
                    label={opt.label}
                  />
                ))}
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Enhance toggle */}
              <FormControlLabel
                control={<Switch checked={enhance} onChange={(e) => setEnhance(e.target.checked)} />}
                label="AI Enhancement Pass"
              />
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                Runs an additional AI pass to improve content structure and readability
              </Typography>

              {/* Launch button */}
              <Button
                variant="contained"
                fullWidth
                startIcon={createMutation.isPending ? <CircularProgress size={18} /> : <RocketLaunchIcon />}
                onClick={handleLaunch}
                disabled={repos.length === 0 || targets.length === 0 || createMutation.isPending}
                size="large"
              >
                {createMutation.isPending ? 'Launching...' : `Scrape ${repos.length} Repo${repos.length !== 1 ? 's' : ''}`}
              </Button>

              {createMutation.isError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {createMutation.error?.message || 'Failed to create job'}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Right panel: Job history */}
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1 }}>
                Job History
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5, mb: 2, flexWrap: 'wrap' }}>
                {STATUS_TABS.map((tab) => (
                  <Chip
                    key={tab.value}
                    label={tab.label}
                    size="small"
                    variant={statusFilter === tab.value ? 'filled' : 'outlined'}
                    color={statusFilter === tab.value ? 'primary' : 'default'}
                    onClick={() => setStatusFilter(tab.value)}
                    clickable
                  />
                ))}
              </Box>

              {jobsLoading ? (
                <Box>
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} variant="rectangular" height={80} sx={{ mb: 1, borderRadius: 1 }} />
                  ))}
                </Box>
              ) : !jobsData?.items.length ? (
                <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                  No scrape jobs yet. Add repos and launch your first job.
                </Typography>
              ) : (
                jobsData.items.map((job) => (
                  <Card key={job.id} variant="outlined" sx={{ mb: 1.5 }}>
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      {/* Job header */}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip
                            label={job.status}
                            size="small"
                            color={STATUS_COLORS[job.status] || 'default'}
                          />
                          <Typography variant="body2" color="text.secondary">
                            {new Date(job.created_at).toLocaleString()}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          {(job.status === ScrapeJobStatus.RUNNING || job.status === ScrapeJobStatus.PENDING) && (
                            <Tooltip title="Cancel job">
                              <IconButton size="small" onClick={() => cancelMutation.mutate(job.id)} disabled={cancelMutation.isPending}>
                                <CancelIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          {job.status === ScrapeJobStatus.FAILED && (
                            <Tooltip title="Retry job">
                              <IconButton size="small" onClick={() => retryMutation.mutate(job.id)} disabled={retryMutation.isPending}>
                                <ReplayIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Delete job">
                            <IconButton size="small" onClick={() => deleteMutation.mutate(job.id)} disabled={deleteMutation.isPending}>
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </Box>

                      {/* Repos */}
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
                        {job.repos.map((repo) => (
                          <Chip key={repo} label={repo} size="small" variant="outlined" icon={<GitHubIcon />} />
                        ))}
                        {job.enhance && <Chip label="Enhanced" size="small" color="secondary" variant="outlined" />}
                      </Box>

                      {/* Progress bar for running jobs */}
                      {(job.status === ScrapeJobStatus.RUNNING || job.status === ScrapeJobStatus.PENDING) && (
                        <Box sx={{ mb: 1 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              {job.current_step}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {job.progress}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant={job.progress > 0 ? 'determinate' : 'indeterminate'}
                            value={job.progress}
                          />
                        </Box>
                      )}

                      {/* Error */}
                      {job.status === ScrapeJobStatus.FAILED && job.error && (
                        <Alert severity="error" sx={{ mt: 1, py: 0 }}>
                          <Typography variant="caption">{job.error}</Typography>
                        </Alert>
                      )}

                      {/* Download + Preview links for completed jobs */}
                      {job.status === ScrapeJobStatus.COMPLETED && job.output_files.length > 0 && (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                          {job.output_files.map((filename) => (
                            <Box key={filename} sx={{ display: 'flex', gap: 0.5 }}>
                              <Button
                                size="small"
                                variant="outlined"
                                startIcon={<PreviewIcon />}
                                onClick={async () => {
                                  try {
                                    const data = await previewFile(job.id, filename);
                                    setPreviewData({ filename, content: data.content });
                                  } catch { /* handled by toast */ }
                                }}
                              >
                                Preview
                              </Button>
                              <Button
                                size="small"
                                variant="outlined"
                                startIcon={<DownloadIcon />}
                                onClick={async () => {
                                  try {
                                    const url = await getSignedDownloadUrl(job.id, filename);
                                    window.open(url, '_blank');
                                  } catch { /* handled by interceptor */ }
                                }}
                              >
                                {filename}
                              </Button>
                            </Box>
                          ))}
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Preview dialog */}
      {previewData && (
        <Card sx={{ position: 'fixed', bottom: 16, right: 16, left: 16, maxHeight: '50vh', overflow: 'auto', zIndex: 1200, boxShadow: 8 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle2">{previewData.filename}</Typography>
              <Button size="small" onClick={() => setPreviewData(null)}>Close</Button>
            </Box>
            <Divider sx={{ mb: 1 }} />
            <Typography
              variant="body2"
              component="pre"
              sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.8rem', maxHeight: '35vh', overflow: 'auto' }}
            >
              {previewData.content}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Catalogue Drawer */}
      <SkillCatalogueDrawer
        open={catalogueOpen}
        onClose={() => setCatalogueOpen(false)}
        selectedRepos={repos}
        onToggle={(repo) => {
          setRepos((prev) =>
            prev.includes(repo) ? prev.filter((r) => r !== repo) : [...prev, repo]
          );
        }}
        filter={catalogueFilter}
        onFilterChange={setCatalogueFilter}
      />
    </Box>
  );
}
