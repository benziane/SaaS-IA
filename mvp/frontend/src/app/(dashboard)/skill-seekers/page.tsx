'use client';

import { useState } from 'react';
import {
  GitFork, PlusCircle, Sparkles, XCircle, X,
  Trash2, Download, Eye, RotateCcw, Rocket,
  RefreshCw, Loader2, Check, Package,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from '@/components/ui/sheet';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Switch } from '@/lib/design-hub/components/Switch';
import { Separator } from '@/lib/design-hub/components/Separator';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/lib/design-hub/components/Tooltip';

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
    <Sheet open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <SheetContent side="right" className="w-full sm:max-w-xl md:max-w-2xl flex flex-col p-0">
        {/* Header */}
        <SheetHeader className="px-6 py-4 border-b border-[var(--border)]">
          <SheetTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-[var(--accent)]" />
            Catalogue Claude Skills
          </SheetTitle>
        </SheetHeader>

        {/* Filters */}
        <div className="px-6 py-3 border-b border-[var(--border)]">
          <div className="flex flex-wrap gap-1">
            <button
              type="button"
              onClick={() => onFilterChange('all')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                filter === 'all'
                  ? 'bg-[var(--accent)] text-[var(--bg-app)]'
                  : 'border border-[var(--border)] text-[var(--text-mid)]'
              }`}
            >
              Tous
            </button>
            {ALL_CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => onFilterChange(cat)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  filter === cat
                    ? 'text-white'
                    : 'border text-[var(--text-mid)]'
                }`}
                style={filter === cat
                  ? { backgroundColor: CATEGORY_COLORS[cat] }
                  : { borderColor: CATEGORY_COLORS[cat], color: CATEGORY_COLORS[cat] }
                }
              >
                {CATEGORY_LABELS[cat]}
              </button>
            ))}
          </div>
        </div>

        {/* Cards grid */}
        <div className="flex-1 overflow-auto p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {filtered.map((item) => {
              const isSelected = selectedRepos.includes(item.repo);
              const isDisabled = !isSelected && selectedRepos.length >= 10;
              return (
                <div
                  key={item.repo}
                  className={`surface-card flex flex-col h-full ${isDisabled ? 'opacity-50' : ''}`}
                  style={{
                    borderColor: isSelected ? CATEGORY_COLORS[item.category] : undefined,
                    borderWidth: isSelected ? 2 : 1,
                  }}
                >
                  <div className="flex-1 p-3 pb-1">
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-sm font-semibold leading-tight text-[var(--text-high)]">
                        {item.name}
                      </span>
                      <Badge
                        className="ml-1 text-[0.65rem] h-[18px] shrink-0 text-white"
                        style={{ backgroundColor: CATEGORY_COLORS[item.category] }}
                      >
                        {CATEGORY_LABELS[item.category]}
                      </Badge>
                    </div>
                    <p className="text-xs text-[var(--text-low)] mb-1">{item.repo}</p>
                    <p className="text-xs text-[var(--text-mid)] mb-2">{item.description}</p>
                    <div className="flex flex-wrap gap-1 mb-1">
                      {item.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-[0.6rem] h-4 px-1">{tag}</Badge>
                      ))}
                    </div>
                    <span className="text-xs text-[var(--text-low)]">{formatStars(item.stars)} stars</span>
                  </div>
                  <div className="p-3 pt-1">
                    {isSelected ? (
                      <Button
                        size="sm"
                        variant="outline"
                        className="w-full text-xs text-green-400 border-green-400/30"
                        onClick={() => onToggle(item.repo)}
                      >
                        <Check className="h-3 w-3 mr-1" /> Already added
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        className="w-full text-xs"
                        disabled={isDisabled}
                        onClick={() => onToggle(item.repo)}
                      >
                        Add
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <SheetFooter className="px-6 py-4 border-t border-[var(--border)] flex items-center justify-between">
          <p className="text-sm text-[var(--text-mid)]">
            {pendingCount > 0 ? `${pendingCount} repo${pendingCount > 1 ? 's' : ''} selected` : 'No repos selected'}
          </p>
          <Button onClick={onClose} disabled={pendingCount === 0}>
            <Rocket className="h-4 w-4 mr-1" /> Confirm
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
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

const STATUS_COLORS: Record<string, 'secondary' | 'default' | 'success' | 'destructive' | 'warning'> = {
  pending: 'secondary',
  running: 'default',
  completed: 'success',
  failed: 'destructive',
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
  const [previewData, setPreviewData] = useState<{ filename: string; content: string; truncated?: boolean } | null>(null);

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
    <div className="p-5 space-y-5 animate-enter">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
            <Package className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">Skill Seekers</h1>
            <p className="text-xs text-[var(--text-mid)]">GitHub skill discovery and packaging</p>
          </div>
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button type="button" title="Refresh jobs" onClick={() => refetch()} className="p-2 rounded hover:bg-[var(--bg-elevated)] text-[var(--text-mid)] hover:text-[var(--text-high)] transition-colors">
                <RefreshCw className="h-5 w-5" />
              </button>
            </TooltipTrigger>
            <TooltipContent>Refresh jobs</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* CLI status alert */}
      {!statusLoading && statusData && !statusData.installed && (
        <Alert variant="warning">
          <AlertDescription>
            <strong>skill-seekers CLI not installed.</strong> Running in mock mode.
            Install it with: <code className="font-mono">pip install skill-seekers</code>
          </AlertDescription>
        </Alert>
      )}

      {/* Stats cards */}
      {statsData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Total Jobs', value: statsData.total_jobs, colorClass: 'text-[var(--accent)]' },
            { label: 'Completed', value: statsData.completed, colorClass: 'text-green-400' },
            { label: 'Failed', value: statsData.failed, colorClass: 'text-red-400' },
            { label: 'Repos Scraped', value: statsData.total_repos_scraped, colorClass: 'text-blue-400' },
          ].map((stat) => (
            <div key={stat.label} className="surface-card p-4 text-center">
              <p className={`text-2xl font-bold ${stat.colorClass}`}>{stat.value}</p>
              <p className="text-xs text-[var(--text-low)]">{stat.label}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
        {/* Left panel: Create job form */}
        <div className="md:col-span-5">
          <div className="surface-card p-5">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4 flex items-center gap-2">
              <GitFork className="h-5 w-5" /> New Scrape Job
            </h2>

            {/* Repo input */}
            <div className="flex gap-2 mb-4">
              <div className="flex-1">
                <Input
                  placeholder="e.g. anthropics/claude-code"
                  value={repoInput}
                  onChange={(e) => setRepoInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className={repos.length >= 10 ? 'border-red-500' : ''}
                />
                {repos.length >= 10 && (
                  <p className="text-xs text-red-400 mt-1">Max 10 repos</p>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddRepo}
                disabled={!repoInput.trim() || repos.length >= 10}
                className="px-2"
                title="Add repo"
              >
                <PlusCircle className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCatalogueOpen(true)}
                className="whitespace-nowrap"
              >
                <Sparkles className="h-4 w-4 mr-1" /> Catalogue
              </Button>
            </div>

            {/* Repo chips */}
            {repos.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-4">
                {repos.map((repo) => (
                  <Badge key={repo} variant="secondary" className="text-xs flex items-center gap-1">
                    <GitFork className="h-3 w-3" /> {repo}
                    <button type="button" onClick={() => handleRemoveRepo(repo)} className="ml-0.5 hover:text-red-400">
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}

            <Separator className="my-4" />

            {/* Target checkboxes */}
            <h3 className="text-sm font-semibold text-[var(--text-high)] mb-2">
              Package Targets
            </h3>
            <div className="flex flex-wrap gap-3 mb-4">
              {TARGET_OPTIONS.map((opt) => (
                <label key={opt.id} className="flex items-center gap-1.5 text-sm text-[var(--text-mid)]">
                  <Checkbox
                    checked={targets.includes(opt.id)}
                    onCheckedChange={() => handleToggleTarget(opt.id)}
                  />
                  {opt.label}
                </label>
              ))}
            </div>

            <Separator className="my-4" />

            {/* Enhance toggle */}
            <label className="flex items-center gap-2 text-sm text-[var(--text-mid)] mb-1">
              <Switch checked={enhance} onCheckedChange={setEnhance} />
              AI Enhancement Pass
            </label>
            <p className="text-xs text-[var(--text-low)] mb-4">
              Runs an additional AI pass to improve content structure and readability
            </p>

            {/* Launch button */}
            <Button
              className="w-full"
              size="lg"
              onClick={handleLaunch}
              disabled={repos.length === 0 || targets.length === 0 || createMutation.isPending}
            >
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Rocket className="h-4 w-4 mr-2" />}
              {createMutation.isPending ? 'Launching...' : `Scrape ${repos.length} Repo${repos.length !== 1 ? 's' : ''}`}
            </Button>

            {createMutation.isError && (
              <Alert variant="destructive" className="mt-4">
                <AlertDescription>
                  {createMutation.error?.message || 'Failed to create job'}
                </AlertDescription>
              </Alert>
            )}
          </div>
        </div>

        {/* Right panel: Job history */}
        <div className="md:col-span-7">
          <div className="surface-card p-5">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-2">
              Job History
            </h2>
            <div className="flex gap-1 mb-4 flex-wrap">
              {STATUS_TABS.map((tab) => (
                <button
                  key={tab.value}
                  type="button"
                  onClick={() => setStatusFilter(tab.value)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                    statusFilter === tab.value
                      ? 'bg-[var(--accent)] text-[var(--bg-app)]'
                      : 'border border-[var(--border)] text-[var(--text-mid)] hover:bg-[var(--bg-elevated)]'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {jobsLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-20 rounded" />
                ))}
              </div>
            ) : !jobsData?.items.length ? (
              <p className="text-[var(--text-mid)] py-8 text-center">
                No scrape jobs yet. Add repos and launch your first job.
              </p>
            ) : (
              jobsData.items.map((job) => (
                <div key={job.id} className="surface-card p-4 mb-3 border border-[var(--border)]">
                  {/* Job header */}
                  <div className="flex justify-between items-center mb-1">
                    <div className="flex items-center gap-2">
                      <Badge variant={STATUS_COLORS[job.status] || 'secondary'}>
                        {job.status}
                      </Badge>
                      <span className="text-sm text-[var(--text-mid)]">
                        {new Date(job.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex gap-1">
                      {(job.status === ScrapeJobStatus.RUNNING || job.status === ScrapeJobStatus.PENDING) && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button type="button" title="Cancel job" className="p-1 rounded hover:bg-[var(--bg-elevated)] text-[var(--text-mid)]" onClick={() => cancelMutation.mutate(job.id)} disabled={cancelMutation.isPending}>
                                <XCircle className="h-4 w-4" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent>Cancel job</TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                      {job.status === ScrapeJobStatus.FAILED && (
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button type="button" title="Retry job" className="p-1 rounded hover:bg-[var(--bg-elevated)] text-[var(--text-mid)]" onClick={() => retryMutation.mutate(job.id)} disabled={retryMutation.isPending}>
                                <RotateCcw className="h-4 w-4" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent>Retry job</TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                      )}
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button type="button" title="Delete job" className="p-1 rounded hover:bg-[var(--bg-elevated)] text-[var(--text-mid)]" onClick={() => deleteMutation.mutate(job.id)} disabled={deleteMutation.isPending}>
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent>Delete job</TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                  </div>

                  {/* Repos */}
                  <div className="flex flex-wrap gap-1 mb-2">
                    {job.repos.map((repo) => (
                      <Badge key={repo} variant="outline" className="text-xs flex items-center gap-1">
                        <GitFork className="h-3 w-3" /> {repo}
                      </Badge>
                    ))}
                    {job.enhance && <Badge variant="outline" className="text-xs text-purple-400 border-purple-400/30">Enhanced</Badge>}
                  </div>

                  {/* Progress bar for running jobs */}
                  {(job.status === ScrapeJobStatus.RUNNING || job.status === ScrapeJobStatus.PENDING) && (
                    <div className="mb-2">
                      <div className="flex justify-between mb-1">
                        <span className="text-xs text-[var(--text-low)]">{job.current_step}</span>
                        <span className="text-xs text-[var(--text-low)]">{job.progress}%</span>
                      </div>
                      <Progress value={job.progress > 0 ? job.progress : undefined} className="h-1.5" />
                    </div>
                  )}

                  {/* Error */}
                  {job.status === ScrapeJobStatus.FAILED && job.error && (
                    <Alert variant="destructive" className="mt-2 py-1">
                      <AlertDescription className="text-xs">{job.error}</AlertDescription>
                    </Alert>
                  )}

                  {/* Download + Preview links for completed jobs */}
                  {job.status === ScrapeJobStatus.COMPLETED && job.output_files.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {job.output_files.map((filename) => (
                        <div key={filename} className="flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-xs"
                            onClick={async () => {
                              try {
                                const data = await previewFile(job.id, filename);
                                setPreviewData({ filename, content: data.content, truncated: data.truncated });
                              } catch (err) {
                                setPreviewData({ filename, content: `Error loading preview: ${err instanceof Error ? err.message : 'Unknown error'}`, truncated: false });
                              }
                            }}
                          >
                            <Eye className="h-3 w-3 mr-1" /> Preview
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-xs"
                            onClick={async () => {
                              try {
                                const url = await getSignedDownloadUrl(job.id, filename);
                                window.open(url, '_blank');
                              } catch (err) {
                                alert(`Download failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
                              }
                            }}
                          >
                            <Download className="h-3 w-3 mr-1" /> {filename}
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Preview dialog */}
      {previewData && (
        <div className="surface-card fixed bottom-4 right-4 left-4 max-h-[50vh] overflow-auto z-50 shadow-xl p-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-semibold text-[var(--text-high)]">{previewData.filename}</span>
            <Button size="sm" variant="ghost" onClick={() => setPreviewData(null)}>Close</Button>
          </div>
          {previewData.truncated && (
            <Alert variant="info" className="mb-2 py-1">
              <AlertDescription className="text-xs">Preview truncated. Download the full file for complete content.</AlertDescription>
            </Alert>
          )}
          <Separator className="mb-2" />
          <pre className="whitespace-pre-wrap font-mono text-xs max-h-[35vh] overflow-auto text-[var(--text-mid)]">
            {previewData.content}
          </pre>
        </div>
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
    </div>
  );
}
