'use client';

import { useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  Divider, FormControl, Grid, IconButton, InputLabel, LinearProgress,
  MenuItem, Select, Skeleton, Tab, Tabs, TextField, Tooltip, Typography,
} from '@mui/material';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import CodeIcon from '@mui/icons-material/Code';
import DeleteIcon from '@mui/icons-material/Delete';
import FolderIcon from '@mui/icons-material/Folder';
import GitHubIcon from '@mui/icons-material/GitHub';
import GradeIcon from '@mui/icons-material/Grade';
import LayersIcon from '@mui/icons-material/Layers';
import RefreshIcon from '@mui/icons-material/Refresh';
import SearchIcon from '@mui/icons-material/Search';
import SecurityIcon from '@mui/icons-material/Security';
import WarningIcon from '@mui/icons-material/Warning';

import { useRepoAnalyses, useRepoAnalyzerStatus } from '@/features/repo-analyzer/hooks/useRepoAnalyzer';
import { useCreateAnalysis, useDeleteAnalysis } from '@/features/repo-analyzer/hooks/useRepoAnalyzerMutations';
import { AnalysisStatus } from '@/features/repo-analyzer/types';
import type { AnalysisDepth, AnalysisType, RepoAnalysis, AnalysisResults } from '@/features/repo-analyzer/types';

const ANALYSIS_TYPE_OPTIONS: { id: AnalysisType; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'structure', label: 'Structure' },
  { id: 'tech_stack', label: 'Tech Stack' },
  { id: 'quality', label: 'Quality' },
  { id: 'dependencies', label: 'Dependencies' },
  { id: 'security', label: 'Security' },
  { id: 'documentation', label: 'Documentation' },
];

const DEPTH_OPTIONS: { id: AnalysisDepth; label: string; desc: string }[] = [
  { id: 'quick', label: 'Quick', desc: 'README + package files' },
  { id: 'standard', label: 'Standard', desc: '+ full source scan' },
  { id: 'deep', label: 'Deep', desc: '+ AI documentation analysis' },
];

const STATUS_COLORS: Record<string, 'default' | 'info' | 'success' | 'error'> = {
  pending: 'default',
  running: 'info',
  completed: 'success',
  failed: 'error',
};

const GRADE_COLORS: Record<string, string> = {
  'A': '#4caf50',
  'A-': '#66bb6a',
  'B+': '#8bc34a',
  'B': '#cddc39',
  'B-': '#ffeb3b',
  'C': '#ff9800',
  'D': '#ff5722',
  'F': '#f44336',
};

function QualityGauge({ score, grade }: { score: number; grade: string }) {
  const color = GRADE_COLORS[grade] || '#9e9e9e';
  return (
    <Box sx={{ position: 'relative', display: 'inline-flex' }}>
      <CircularProgress
        variant="determinate"
        value={score}
        size={100}
        thickness={6}
        sx={{ color, '& .MuiCircularProgress-circle': { strokeLinecap: 'round' } }}
      />
      <Box sx={{
        top: 0, left: 0, bottom: 0, right: 0,
        position: 'absolute', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <Typography variant="h5" sx={{ fontWeight: 700, color }}>{grade}</Typography>
        <Typography variant="caption" color="text.secondary">{score}/100</Typography>
      </Box>
    </Box>
  );
}

function ResultTabs({ results }: { results: AnalysisResults }) {
  const [tab, setTab] = useState(0);

  const tabs: { label: string; key: string; icon: React.ReactElement }[] = [];
  if (results.structure) tabs.push({ label: 'Structure', key: 'structure', icon: <FolderIcon /> });
  if (results.tech_stack) tabs.push({ label: 'Tech Stack', key: 'tech_stack', icon: <CodeIcon /> });
  if (results.quality) tabs.push({ label: 'Quality', key: 'quality', icon: <GradeIcon /> });
  if (results.dependencies) tabs.push({ label: 'Dependencies', key: 'dependencies', icon: <LayersIcon /> });
  if (results.security) tabs.push({ label: 'Security', key: 'security', icon: <SecurityIcon /> });
  if (results.documentation) tabs.push({ label: 'Docs', key: 'documentation', icon: <AnalyticsIcon /> });

  if (tabs.length === 0) return <Typography color="text.secondary">No results available</Typography>;

  const currentTab = tabs[tab] || tabs[0];

  return (
    <Box>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" scrollButtons="auto" sx={{ mb: 2 }}>
        {tabs.map((t) => (
          <Tab key={t.key} label={t.label} icon={t.icon} iconPosition="start" sx={{ minHeight: 48 }} />
        ))}
      </Tabs>

      {/* Structure tab */}
      {currentTab.key === 'structure' && results.structure && (
        <Box>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Total Files</Typography>
              <Typography variant="h6">{results.structure.total_files.toLocaleString()}</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Total Lines</Typography>
              <Typography variant="h6">{results.structure.total_lines.toLocaleString()}</Typography>
            </Grid>
          </Grid>
          {results.structure.key_files.length > 0 && (
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Key Files</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {results.structure.key_files.map((f) => (
                  <Chip key={f} label={f} size="small" variant="outlined" />
                ))}
              </Box>
            </Box>
          )}
          {results.structure.extension_counts && Object.keys(results.structure.extension_counts).length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>File Extensions</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {Object.entries(results.structure.extension_counts).slice(0, 15).map(([ext, count]) => (
                  <Chip key={ext} label={`${ext}: ${count}`} size="small" variant="outlined" />
                ))}
              </Box>
            </Box>
          )}
        </Box>
      )}

      {/* Tech Stack tab */}
      {currentTab.key === 'tech_stack' && results.tech_stack && (
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>Languages</Typography>
          <Box sx={{ mb: 2 }}>
            {Object.entries(results.tech_stack.languages).map(([lang, pct]) => (
              <Box key={lang} sx={{ mb: 0.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">{lang}</Typography>
                  <Typography variant="body2" color="text.secondary">{pct}%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={pct} sx={{ height: 6, borderRadius: 3 }} />
              </Box>
            ))}
          </Box>
          {results.tech_stack.frameworks.length > 0 && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="subtitle2" sx={{ mb: 0.5 }}>Frameworks</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {results.tech_stack.frameworks.map((f) => (
                  <Chip key={f} label={f} size="small" color="primary" variant="outlined" />
                ))}
              </Box>
            </Box>
          )}
          {results.tech_stack.build_tools.length > 0 && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="subtitle2" sx={{ mb: 0.5 }}>Build Tools</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {results.tech_stack.build_tools.map((t) => (
                  <Chip key={t} label={t} size="small" variant="outlined" />
                ))}
              </Box>
            </Box>
          )}
          <Box sx={{ display: 'flex', gap: 3, mt: 1 }}>
            <Box>
              <Typography variant="caption" color="text.secondary">Package Manager</Typography>
              <Typography variant="body2">{results.tech_stack.package_manager}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Runtime</Typography>
              <Typography variant="body2">{results.tech_stack.runtime}</Typography>
            </Box>
          </Box>
        </Box>
      )}

      {/* Quality tab */}
      {currentTab.key === 'quality' && results.quality && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 2 }}>
            <QualityGauge score={results.quality.score} grade={results.quality.grade} />
            <Box>
              {results.quality.issues.length > 0 && (
                <Box sx={{ mb: 1 }}>
                  <Typography variant="subtitle2" color="error">Issues</Typography>
                  {results.quality.issues.map((issue, i) => (
                    <Typography key={i} variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <WarningIcon fontSize="inherit" color="error" /> {issue}
                    </Typography>
                  ))}
                </Box>
              )}
            </Box>
          </Box>
          {results.quality.recommendations.length > 0 && (
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 0.5 }}>Recommendations</Typography>
              {results.quality.recommendations.map((rec, i) => (
                <Typography key={i} variant="body2" color="text.secondary">
                  {i + 1}. {rec}
                </Typography>
              ))}
            </Box>
          )}
        </Box>
      )}

      {/* Dependencies tab */}
      {currentTab.key === 'dependencies' && results.dependencies && (
        <Box>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={4}>
              <Typography variant="body2" color="text.secondary">Total</Typography>
              <Typography variant="h6">{results.dependencies.total}</Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography variant="body2" color="text.secondary">Direct</Typography>
              <Typography variant="h6">{results.dependencies.direct}</Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography variant="body2" color="text.secondary">Dev</Typography>
              <Typography variant="h6">{results.dependencies.dev}</Typography>
            </Grid>
          </Grid>
          {results.dependencies.outdated.length > 0 && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="subtitle2" color="warning.main">Outdated</Typography>
              {results.dependencies.outdated.map((d, i) => (
                <Typography key={i} variant="body2">{d}</Typography>
              ))}
            </Box>
          )}
          {results.dependencies.vulnerabilities.length > 0 && (
            <Alert severity="error" sx={{ mt: 1 }}>
              {results.dependencies.vulnerabilities.length} vulnerability(ies) found
            </Alert>
          )}
          {results.dependencies.outdated.length === 0 && results.dependencies.vulnerabilities.length === 0 && (
            <Alert severity="success">No outdated packages or vulnerabilities detected</Alert>
          )}
        </Box>
      )}

      {/* Security tab */}
      {currentTab.key === 'security' && results.security && (
        <Box>
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <Chip
              label={`Risk: ${results.security.risk_level.toUpperCase()}`}
              color={
                results.security.risk_level === 'low' ? 'success' :
                results.security.risk_level === 'medium' ? 'warning' :
                'error'
              }
            />
            {results.security.secrets_found > 0 && (
              <Chip label={`${results.security.secrets_found} secret(s) found`} color="error" />
            )}
            {results.security.env_files_committed > 0 && (
              <Chip label={`${results.security.env_files_committed} .env file(s) committed`} color="warning" />
            )}
          </Box>
          {results.security.issues.length > 0 ? (
            results.security.issues.map((issue, i) => (
              <Alert key={i} severity={issue.severity === 'critical' ? 'error' : 'warning'} sx={{ mb: 1 }}>
                <Typography variant="body2"><strong>{issue.type}</strong>: {issue.message}</Typography>
              </Alert>
            ))
          ) : (
            <Alert severity="success">No security issues detected</Alert>
          )}
        </Box>
      )}

      {/* Documentation tab */}
      {currentTab.key === 'documentation' && results.documentation && (
        <Box>
          {results.documentation.architecture_overview && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 0.5 }}>Architecture Overview</Typography>
              <Typography variant="body2">{results.documentation.architecture_overview}</Typography>
            </Box>
          )}
          {results.documentation.readme_suggestions.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 0.5 }}>README Suggestions</Typography>
              {results.documentation.readme_suggestions.map((s, i) => (
                <Typography key={i} variant="body2" color="text.secondary">{i + 1}. {s}</Typography>
              ))}
            </Box>
          )}
          {results.documentation.api_docs_suggestions.length > 0 && (
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 0.5 }}>API Docs Suggestions</Typography>
              {results.documentation.api_docs_suggestions.map((s, i) => (
                <Typography key={i} variant="body2" color="text.secondary">{i + 1}. {s}</Typography>
              ))}
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
}

export default function RepoAnalyzerPage() {
  const { data: statusData, isLoading: statusLoading } = useRepoAnalyzerStatus();
  const { data: analysesData, isLoading: analysesLoading, refetch } = useRepoAnalyses();
  const createMutation = useCreateAnalysis();
  const deleteMutation = useDeleteAnalysis();

  // Form state
  const [repoUrl, setRepoUrl] = useState('');
  const [analysisTypes, setAnalysisTypes] = useState<AnalysisType[]>(['all']);
  const [depth, setDepth] = useState<AnalysisDepth>('standard');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const handleAnalyze = () => {
    if (!repoUrl.trim()) return;
    createMutation.mutate(
      { repo_url: repoUrl.trim(), analysis_types: analysisTypes, depth },
      {
        onSuccess: () => {
          setRepoUrl('');
        },
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAnalyze();
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SearchIcon color="primary" /> Repo Analyzer
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Analyze GitHub repositories: tech stack, quality scoring, dependencies, security
          </Typography>
        </Box>
        <Tooltip title="Refresh analyses">
          <IconButton onClick={() => refetch()}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Git status alert */}
      {!statusLoading && statusData && !statusData.installed && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <strong>git not installed.</strong> Running in mock mode with sample data.
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Left panel: Analysis form */}
        <Grid item xs={12} md={5}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <GitHubIcon /> Analyze Repository
              </Typography>

              {/* Repo URL input */}
              <TextField
                fullWidth
                size="small"
                label="Repository URL"
                placeholder="https://github.com/owner/repo or owner/repo"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyDown={handleKeyDown}
                sx={{ mb: 2 }}
              />

              {/* Analysis types */}
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel>Analysis Types</InputLabel>
                <Select
                  multiple
                  value={analysisTypes}
                  onChange={(e) => setAnalysisTypes(e.target.value as AnalysisType[])}
                  label="Analysis Types"
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((v) => (
                        <Chip key={v} label={ANALYSIS_TYPE_OPTIONS.find((o) => o.id === v)?.label || v} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {ANALYSIS_TYPE_OPTIONS.map((opt) => (
                    <MenuItem key={opt.id} value={opt.id}>{opt.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Depth selector */}
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel>Analysis Depth</InputLabel>
                <Select
                  value={depth}
                  onChange={(e) => setDepth(e.target.value as AnalysisDepth)}
                  label="Analysis Depth"
                >
                  {DEPTH_OPTIONS.map((opt) => (
                    <MenuItem key={opt.id} value={opt.id}>
                      {opt.label} - {opt.desc}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Analyze button */}
              <Button
                variant="contained"
                fullWidth
                startIcon={createMutation.isPending ? <CircularProgress size={18} /> : <AnalyticsIcon />}
                onClick={handleAnalyze}
                disabled={!repoUrl.trim() || createMutation.isPending}
                size="large"
              >
                {createMutation.isPending ? 'Analyzing...' : 'Analyze Repository'}
              </Button>

              {createMutation.isError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {createMutation.error?.message || 'Failed to start analysis'}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Right panel: Analysis history */}
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Analysis History
              </Typography>

              {analysesLoading ? (
                <Box>
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} variant="rectangular" height={80} sx={{ mb: 1, borderRadius: 1 }} />
                  ))}
                </Box>
              ) : !analysesData?.items.length ? (
                <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                  No analyses yet. Enter a repo URL and start your first analysis.
                </Typography>
              ) : (
                analysesData.items.map((analysis: RepoAnalysis) => (
                  <Card key={analysis.id} variant="outlined" sx={{ mb: 1.5 }}>
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      {/* Header */}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1, minWidth: 0 }}>
                          <Chip
                            label={analysis.status}
                            size="small"
                            color={STATUS_COLORS[analysis.status] || 'default'}
                          />
                          <Typography variant="body2" fontWeight={600} noWrap>
                            {analysis.repo_name}
                          </Typography>
                          <Chip label={analysis.depth} size="small" variant="outlined" />
                        </Box>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          {analysis.status === AnalysisStatus.COMPLETED && (
                            <Tooltip title={expandedId === analysis.id ? 'Collapse' : 'View Results'}>
                              <IconButton
                                size="small"
                                onClick={() => setExpandedId(expandedId === analysis.id ? null : analysis.id)}
                              >
                                <AnalyticsIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              onClick={() => deleteMutation.mutate(analysis.id)}
                              disabled={deleteMutation.isPending}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </Box>

                      {/* Repo URL */}
                      <Typography variant="caption" color="text.secondary" noWrap>
                        {analysis.repo_url} - {new Date(analysis.created_at).toLocaleString()}
                      </Typography>

                      {/* Quality badge for completed analyses */}
                      {analysis.status === AnalysisStatus.COMPLETED && analysis.results?.quality && (
                        <Box sx={{ mt: 0.5, display: 'flex', gap: 1 }}>
                          <Chip
                            label={`${analysis.results.quality.grade} (${analysis.results.quality.score}/100)`}
                            size="small"
                            sx={{
                              bgcolor: GRADE_COLORS[analysis.results.quality.grade] || '#9e9e9e',
                              color: 'white',
                              fontWeight: 600,
                            }}
                          />
                          {analysis.results.tech_stack?.frameworks.slice(0, 3).map((f) => (
                            <Chip key={f} label={f} size="small" variant="outlined" />
                          ))}
                        </Box>
                      )}

                      {/* Progress bar for running */}
                      {(analysis.status === AnalysisStatus.RUNNING || analysis.status === AnalysisStatus.PENDING) && (
                        <Box sx={{ mt: 1 }}>
                          <LinearProgress
                            variant={analysis.status === AnalysisStatus.RUNNING ? 'indeterminate' : 'indeterminate'}
                          />
                        </Box>
                      )}

                      {/* Error */}
                      {analysis.status === AnalysisStatus.FAILED && analysis.error && (
                        <Alert severity="error" sx={{ mt: 1, py: 0 }}>
                          <Typography variant="caption">{analysis.error}</Typography>
                        </Alert>
                      )}

                      {/* Expanded results */}
                      {expandedId === analysis.id && analysis.results && (
                        <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                          <ResultTabs results={analysis.results} />
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
