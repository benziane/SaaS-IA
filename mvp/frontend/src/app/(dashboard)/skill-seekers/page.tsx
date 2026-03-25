'use client';

import { useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Checkbox, Chip, CircularProgress,
  Divider, FormControlLabel, Grid, IconButton, LinearProgress, Skeleton,
  Switch, TextField, Tooltip, Typography,
} from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import DeleteIcon from '@mui/icons-material/Delete';
import DownloadIcon from '@mui/icons-material/Download';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import TerminalIcon from '@mui/icons-material/Terminal';
import RefreshIcon from '@mui/icons-material/Refresh';

import { useSkillSeekersJobs, useSkillSeekersStatus } from '@/features/skill-seekers/hooks/useSkillSeekers';
import { useCreateScrapeJob, useDeleteScrapeJob } from '@/features/skill-seekers/hooks/useSkillSeekersMutations';
import { getDownloadUrl } from '@/features/skill-seekers/api';
import { ScrapeJobStatus } from '@/features/skill-seekers/types';

const TARGET_OPTIONS = [
  { id: 'claude', label: 'Claude' },
  { id: 'chatgpt', label: 'ChatGPT' },
  { id: 'gemini', label: 'Gemini' },
  { id: 'raw', label: 'Raw Markdown' },
];

const STATUS_COLORS: Record<string, 'default' | 'info' | 'success' | 'error' | 'warning'> = {
  pending: 'default',
  running: 'info',
  completed: 'success',
  failed: 'error',
};

export default function SkillSeekersPage() {
  const { data: statusData, isLoading: statusLoading } = useSkillSeekersStatus();
  const { data: jobsData, isLoading: jobsLoading, refetch } = useSkillSeekersJobs();
  const createMutation = useCreateScrapeJob();
  const deleteMutation = useDeleteScrapeJob();

  // Form state
  const [repoInput, setRepoInput] = useState('');
  const [repos, setRepos] = useState<string[]>([]);
  const [targets, setTargets] = useState<string[]>(['claude']);
  const [enhance, setEnhance] = useState(false);

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
              <Typography variant="h6" sx={{ mb: 2 }}>
                Job History
              </Typography>

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
                        <Tooltip title="Delete job">
                          <IconButton
                            size="small"
                            onClick={() => deleteMutation.mutate(job.id)}
                            disabled={deleteMutation.isPending}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
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

                      {/* Download links for completed jobs */}
                      {job.status === ScrapeJobStatus.COMPLETED && job.output_files.length > 0 && (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                          {job.output_files.map((filename) => (
                            <Button
                              key={filename}
                              size="small"
                              variant="outlined"
                              startIcon={<DownloadIcon />}
                              href={getDownloadUrl(job.id, filename)}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {filename}
                            </Button>
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
    </Box>
  );
}
