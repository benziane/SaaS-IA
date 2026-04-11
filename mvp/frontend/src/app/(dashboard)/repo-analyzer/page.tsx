'use client';

import { useState } from 'react';
import {
  BarChart3, Code, Folder, GitFork, Award, Layers,
  Shield, AlertTriangle, RefreshCw, Trash2, Loader2, FolderGit2,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/lib/design-hub/components/Tabs';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/lib/design-hub/components/Tooltip';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/lib/design-hub/components/Select';

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

const STATUS_COLORS: Record<string, 'secondary' | 'default' | 'success' | 'destructive'> = {
  pending: 'secondary',
  running: 'default',
  completed: 'success',
  failed: 'destructive',
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
    <div className="relative inline-flex items-center justify-center">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="42" fill="none" stroke="var(--bg-elevated)" strokeWidth="6" />
        <circle
          cx="50" cy="50" r="42" fill="none"
          stroke={color} strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={`${score * 2.64} ${264 - score * 2.64}`}
          transform="rotate(-90 50 50)"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold" style={{ color }}>{grade}</span>
        <span className="text-xs text-[var(--text-low)]">{score}/100</span>
      </div>
    </div>
  );
}

function ResultTabs({ results }: { results: AnalysisResults }) {
  const tabs: { label: string; key: string; icon: React.ReactElement }[] = [];
  if (results.structure) tabs.push({ label: 'Structure', key: 'structure', icon: <Folder className="h-4 w-4" /> });
  if (results.tech_stack) tabs.push({ label: 'Tech Stack', key: 'tech_stack', icon: <Code className="h-4 w-4" /> });
  if (results.quality) tabs.push({ label: 'Quality', key: 'quality', icon: <Award className="h-4 w-4" /> });
  if (results.dependencies) tabs.push({ label: 'Dependencies', key: 'dependencies', icon: <Layers className="h-4 w-4" /> });
  if (results.security) tabs.push({ label: 'Security', key: 'security', icon: <Shield className="h-4 w-4" /> });
  if (results.documentation) tabs.push({ label: 'Docs', key: 'documentation', icon: <BarChart3 className="h-4 w-4" /> });

  if (tabs.length === 0) return <p className="text-[var(--text-mid)]">No results available</p>;

  return (
    <Tabs defaultValue={tabs[0]!.key}>
      <TabsList className="mb-4">
        {tabs.map((t) => (
          <TabsTrigger key={t.key} value={t.key} className="flex items-center gap-1.5">
            {t.icon} {t.label}
          </TabsTrigger>
        ))}
      </TabsList>

      {/* Structure tab */}
      {results.structure && (
        <TabsContent value="structure">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-[var(--text-mid)]">Total Files</p>
              <p className="text-lg font-semibold text-[var(--text-high)]">{results.structure.total_files.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-[var(--text-mid)]">Total Lines</p>
              <p className="text-lg font-semibold text-[var(--text-high)]">{results.structure.total_lines.toLocaleString()}</p>
            </div>
          </div>
          {results.structure.key_files.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-[var(--text-high)] mb-2">Key Files</h4>
              <div className="flex flex-wrap gap-1">
                {results.structure.key_files.map((f) => (
                  <Badge key={f} variant="outline" className="text-xs">{f}</Badge>
                ))}
              </div>
            </div>
          )}
          {results.structure.extension_counts && Object.keys(results.structure.extension_counts).length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-[var(--text-high)] mb-2">File Extensions</h4>
              <div className="flex flex-wrap gap-1">
                {Object.entries(results.structure.extension_counts).slice(0, 15).map(([ext, count]) => (
                  <Badge key={ext} variant="outline" className="text-xs">{ext}: {count}</Badge>
                ))}
              </div>
            </div>
          )}
        </TabsContent>
      )}

      {/* Tech Stack tab */}
      {results.tech_stack && (
        <TabsContent value="tech_stack">
          <h4 className="text-sm font-semibold text-[var(--text-high)] mb-2">Languages</h4>
          <div className="mb-4">
            {Object.entries(results.tech_stack.languages).map(([lang, pct]) => (
              <div key={lang} className="mb-1.5">
                <div className="flex justify-between">
                  <span className="text-sm text-[var(--text-high)]">{lang}</span>
                  <span className="text-sm text-[var(--text-mid)]">{pct}%</span>
                </div>
                <Progress value={pct} className="h-1.5" />
              </div>
            ))}
          </div>
          {results.tech_stack.frameworks.length > 0 && (
            <div className="mb-2">
              <h4 className="text-sm font-semibold text-[var(--text-high)] mb-1">Frameworks</h4>
              <div className="flex flex-wrap gap-1">
                {results.tech_stack.frameworks.map((f) => (
                  <Badge key={f} variant="outline" className="text-xs border-blue-500/30 text-blue-400">{f}</Badge>
                ))}
              </div>
            </div>
          )}
          {results.tech_stack.build_tools.length > 0 && (
            <div className="mb-2">
              <h4 className="text-sm font-semibold text-[var(--text-high)] mb-1">Build Tools</h4>
              <div className="flex flex-wrap gap-1">
                {results.tech_stack.build_tools.map((t) => (
                  <Badge key={t} variant="outline" className="text-xs">{t}</Badge>
                ))}
              </div>
            </div>
          )}
          <div className="flex gap-6 mt-2">
            <div>
              <span className="text-xs text-[var(--text-low)]">Package Manager</span>
              <p className="text-sm text-[var(--text-high)]">{results.tech_stack.package_manager}</p>
            </div>
            <div>
              <span className="text-xs text-[var(--text-low)]">Runtime</span>
              <p className="text-sm text-[var(--text-high)]">{results.tech_stack.runtime}</p>
            </div>
          </div>
        </TabsContent>
      )}

      {/* Quality tab */}
      {results.quality && (
        <TabsContent value="quality">
          <div className="flex items-center gap-6 mb-4">
            <QualityGauge score={results.quality.score} grade={results.quality.grade} />
            <div>
              {results.quality.issues.length > 0 && (
                <div className="mb-2">
                  <h4 className="text-sm font-semibold text-red-400">Issues</h4>
                  {results.quality.issues.map((issue, i) => (
                    <p key={i} className="text-sm flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3 text-red-400" /> {issue}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
          {results.quality.recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-[var(--text-high)] mb-1">Recommendations</h4>
              {results.quality.recommendations.map((rec, i) => (
                <p key={i} className="text-sm text-[var(--text-mid)]">
                  {i + 1}. {rec}
                </p>
              ))}
            </div>
          )}
        </TabsContent>
      )}

      {/* Dependencies tab */}
      {results.dependencies && (
        <TabsContent value="dependencies">
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <p className="text-sm text-[var(--text-mid)]">Total</p>
              <p className="text-lg font-semibold text-[var(--text-high)]">{results.dependencies.total}</p>
            </div>
            <div>
              <p className="text-sm text-[var(--text-mid)]">Direct</p>
              <p className="text-lg font-semibold text-[var(--text-high)]">{results.dependencies.direct}</p>
            </div>
            <div>
              <p className="text-sm text-[var(--text-mid)]">Dev</p>
              <p className="text-lg font-semibold text-[var(--text-high)]">{results.dependencies.dev}</p>
            </div>
          </div>
          {results.dependencies.outdated.length > 0 && (
            <div className="mb-2">
              <h4 className="text-sm font-semibold text-amber-400">Outdated</h4>
              {results.dependencies.outdated.map((d, i) => (
                <p key={i} className="text-sm text-[var(--text-high)]">{d}</p>
              ))}
            </div>
          )}
          {results.dependencies.vulnerabilities.length > 0 && (
            <Alert variant="destructive" className="mt-2">
              <AlertDescription>
                {results.dependencies.vulnerabilities.length} vulnerability(ies) found
              </AlertDescription>
            </Alert>
          )}
          {results.dependencies.outdated.length === 0 && results.dependencies.vulnerabilities.length === 0 && (
            <Alert variant="success">
              <AlertDescription>No outdated packages or vulnerabilities detected</AlertDescription>
            </Alert>
          )}
        </TabsContent>
      )}

      {/* Security tab */}
      {results.security && (
        <TabsContent value="security">
          <div className="flex gap-2 mb-4">
            <Badge
              variant={
                results.security.risk_level === 'low' ? 'success' :
                results.security.risk_level === 'medium' ? 'warning' :
                'destructive'
              }
            >
              Risk: {results.security.risk_level.toUpperCase()}
            </Badge>
            {results.security.secrets_found > 0 && (
              <Badge variant="destructive">{results.security.secrets_found} secret(s) found</Badge>
            )}
            {results.security.env_files_committed > 0 && (
              <Badge variant="warning">{results.security.env_files_committed} .env file(s) committed</Badge>
            )}
          </div>
          {results.security.issues.length > 0 ? (
            results.security.issues.map((issue, i) => (
              <Alert key={i} variant={issue.severity === 'critical' ? 'destructive' : 'warning'} className="mb-2">
                <AlertDescription>
                  <strong>{issue.type}</strong>: {issue.message}
                </AlertDescription>
              </Alert>
            ))
          ) : (
            <Alert variant="success">
              <AlertDescription>No security issues detected</AlertDescription>
            </Alert>
          )}
        </TabsContent>
      )}

      {/* Documentation tab */}
      {results.documentation && (
        <TabsContent value="documentation">
          {results.documentation.architecture_overview && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-[var(--text-high)] mb-1">Architecture Overview</h4>
              <p className="text-sm text-[var(--text-mid)]">{results.documentation.architecture_overview}</p>
            </div>
          )}
          {results.documentation.readme_suggestions.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-[var(--text-high)] mb-1">README Suggestions</h4>
              {results.documentation.readme_suggestions.map((s, i) => (
                <p key={i} className="text-sm text-[var(--text-mid)]">{i + 1}. {s}</p>
              ))}
            </div>
          )}
          {results.documentation.api_docs_suggestions.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-[var(--text-high)] mb-1">API Docs Suggestions</h4>
              {results.documentation.api_docs_suggestions.map((s, i) => (
                <p key={i} className="text-sm text-[var(--text-mid)]">{i + 1}. {s}</p>
              ))}
            </div>
          )}
        </TabsContent>
      )}
    </Tabs>
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

  const toggleAnalysisType = (type: AnalysisType) => {
    setAnalysisTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  return (
    <div className="p-5 space-y-5 animate-enter">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
            <FolderGit2 className="h-5 w-5 text-[var(--accent)]" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">Repo Analyzer</h1>
            <p className="text-xs text-[var(--text-mid)]">Git repository analysis and metrics</p>
          </div>
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button type="button" title="Refresh analyses" onClick={() => refetch()} className="p-2 rounded hover:bg-[var(--bg-elevated)] text-[var(--text-mid)] hover:text-[var(--text-high)] transition-colors">
                <RefreshCw className="h-5 w-5" />
              </button>
            </TooltipTrigger>
            <TooltipContent>Refresh analyses</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Git status alert */}
      {!statusLoading && statusData && !statusData.installed && (
        <Alert variant="warning">
          <AlertDescription>
            <strong>git not installed.</strong> Running in mock mode with sample data.
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
        {/* Left panel: Analysis form */}
        <div className="md:col-span-5">
          <div className="surface-card p-5">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4 flex items-center gap-2">
              <GitFork className="h-5 w-5" /> Analyze Repository
            </h2>

            {/* Repo URL input */}
            <div className="mb-4">
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Repository URL</label>
              <Input
                placeholder="https://github.com/owner/repo or owner/repo"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyDown={handleKeyDown}
              />
            </div>

            {/* Analysis types */}
            <div className="mb-4">
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Analysis Types</label>
              <div className="flex flex-wrap gap-1">
                {ANALYSIS_TYPE_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => toggleAnalysisType(opt.id)}
                    className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                      analysisTypes.includes(opt.id)
                        ? 'bg-[var(--accent)] text-[var(--bg-app)]'
                        : 'border border-[var(--border)] text-[var(--text-mid)] hover:bg-[var(--bg-elevated)]'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Depth selector */}
            <div className="mb-4">
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Analysis Depth</label>
              <Select value={depth} onValueChange={(v) => setDepth(v as AnalysisDepth)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DEPTH_OPTIONS.map((opt) => (
                    <SelectItem key={opt.id} value={opt.id}>
                      {opt.label} - {opt.desc}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Analyze button */}
            <Button
              className="w-full"
              size="lg"
              onClick={handleAnalyze}
              disabled={!repoUrl.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <BarChart3 className="h-4 w-4 mr-2" />}
              {createMutation.isPending ? 'Analyzing...' : 'Analyze Repository'}
            </Button>

            {createMutation.isError && (
              <Alert variant="destructive" className="mt-4">
                <AlertDescription>
                  {createMutation.error?.message || 'Failed to start analysis'}
                </AlertDescription>
              </Alert>
            )}
          </div>
        </div>

        {/* Right panel: Analysis history */}
        <div className="md:col-span-7">
          <div className="surface-card p-5">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">
              Analysis History
            </h2>

            {analysesLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-20 rounded" />
                ))}
              </div>
            ) : !analysesData?.items.length ? (
              <p className="text-[var(--text-mid)] py-8 text-center">
                No analyses yet. Enter a repo URL and start your first analysis.
              </p>
            ) : (
              analysesData.items.map((analysis: RepoAnalysis) => (
                <div key={analysis.id} className="surface-card p-4 mb-3 border border-[var(--border)]">
                  {/* Header */}
                  <div className="flex justify-between items-center mb-1">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <Badge variant={STATUS_COLORS[analysis.status] || 'secondary'}>
                        {analysis.status}
                      </Badge>
                      <span className="text-sm font-semibold text-[var(--text-high)] truncate">
                        {analysis.repo_name}
                      </span>
                      <Badge variant="outline" className="text-xs">{analysis.depth}</Badge>
                    </div>
                    <div className="flex gap-1">
                      {analysis.status === AnalysisStatus.COMPLETED && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button
                                type="button"
                                title={expandedId === analysis.id ? 'Collapse' : 'View Results'}
                                onClick={() => setExpandedId(expandedId === analysis.id ? null : analysis.id)}
                                className="p-1 rounded hover:bg-[var(--bg-elevated)] text-[var(--text-mid)]"
                              >
                                <BarChart3 className="h-4 w-4" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent>{expandedId === analysis.id ? 'Collapse' : 'View Results'}</TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              title="Delete analysis"
                              onClick={() => deleteMutation.mutate(analysis.id)}
                              disabled={deleteMutation.isPending}
                              className="p-1 rounded hover:bg-[var(--bg-elevated)] text-[var(--text-mid)] disabled:opacity-50"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent>Delete</TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                  </div>

                  {/* Repo URL */}
                  <p className="text-xs text-[var(--text-low)] truncate">
                    {analysis.repo_url} - {new Date(analysis.created_at).toLocaleString()}
                  </p>

                  {/* Quality badge for completed analyses */}
                  {analysis.status === AnalysisStatus.COMPLETED && analysis.results?.quality && (
                    <div className="mt-1 flex gap-2">
                      <Badge
                        className="text-xs font-semibold text-white"
                        style={{
                          backgroundColor: GRADE_COLORS[analysis.results.quality.grade] || '#9e9e9e',
                        }}
                      >
                        {analysis.results.quality.grade} ({analysis.results.quality.score}/100)
                      </Badge>
                      {analysis.results.tech_stack?.frameworks.slice(0, 3).map((f) => (
                        <Badge key={f} variant="outline" className="text-xs">{f}</Badge>
                      ))}
                    </div>
                  )}

                  {/* Progress bar for running */}
                  {(analysis.status === AnalysisStatus.RUNNING || analysis.status === AnalysisStatus.PENDING) && (
                    <div className="mt-2">
                      <div className="h-1.5 w-full bg-[var(--bg-elevated)] rounded-full overflow-hidden">
                        <div className="h-full bg-[var(--accent)] rounded-full animate-pulse" style={{ width: '60%' }} />
                      </div>
                    </div>
                  )}

                  {/* Error */}
                  {analysis.status === AnalysisStatus.FAILED && analysis.error && (
                    <Alert variant="destructive" className="mt-2 py-1">
                      <AlertDescription className="text-xs">{analysis.error}</AlertDescription>
                    </Alert>
                  )}

                  {/* Expanded results */}
                  {expandedId === analysis.id && analysis.results && (
                    <div className="mt-4 pt-4 border-t border-[var(--border)]">
                      <ResultTabs results={analysis.results} />
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
