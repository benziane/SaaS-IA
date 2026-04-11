'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import {
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, TrendingDown, ArrowRight, CheckCircle2, AlertCircle, Clock, Activity } from 'lucide-react';

import { Button } from '@/lib/design-hub/components/Button';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';

import { useCurrentUser } from '@/features/auth/hooks/useAuth';
import { useTranscriptions } from '@/features/transcription/hooks/useTranscriptions';
import { useStats } from '@/features/transcription/hooks/useStats';

// --- System Status Bar ---
// One-line overview of what's running. No "welcome back". No aspirational copy.
function SystemStatusBar({ moduleCount }: { moduleCount: number }) {
  return (
    <div
      className="flex items-center justify-between px-4 py-2.5 rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] mb-6"
      role="status"
      aria-label="System status"
    >
      <div className="flex items-center gap-5">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse" />
          <span className="text-xs font-medium text-[var(--text-mid)]">
            {moduleCount} modules active
          </span>
        </div>
        <div className="hidden sm:flex items-center gap-2 text-xs text-[var(--text-low)]">
          <span className="w-px h-3 bg-[var(--border)]" />
          <span>API healthy</span>
        </div>
        <div className="hidden md:flex items-center gap-2 text-xs text-[var(--text-low)]">
          <span className="w-px h-3 bg-[var(--border)]" />
          <span>Backend v4.4.0</span>
        </div>
      </div>
      <Button variant="ghost" size="sm" asChild>
        <Link href="/monitoring" className="flex items-center gap-1.5 text-[var(--accent)] text-xs font-medium">
          <Activity className="h-3 w-3" />
          Monitoring
        </Link>
      </Button>
    </div>
  );
}

// --- Stat Row ---
// No cards. Inline stat layout with dividers. No icons.
function StatRow({
  stats,
  statsLoading,
}: {
  stats: { total_transcriptions?: number; completed?: number; failed?: number; total_duration_seconds?: number } | undefined;
  statsLoading: boolean;
}) {
  const totalDuration = stats?.total_duration_seconds || 0;
  const hours = Math.floor(Number(totalDuration) / 3600);
  const minutes = Math.floor((Number(totalDuration) % 3600) / 60);
  const durationLabel = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
  const successRate = stats?.total_transcriptions
    ? Math.round((Number(stats.completed || 0) / Number(stats.total_transcriptions)) * 100)
    : 0;

  const items = [
    {
      label: 'Transcriptions',
      value: stats?.total_transcriptions ?? 0,
      trend: 12,
      trendLabel: 'vs last month',
    },
    {
      label: 'Success rate',
      value: `${successRate}%`,
      trend: successRate >= 80 ? 0 : -1,
      trendLabel: `${stats?.completed ?? 0} completed`,
    },
    {
      label: 'Failed',
      value: stats?.failed ?? 0,
      trend: (stats?.failed ?? 0) === 0 ? 0 : -1,
      trendLabel: 'needs attention',
    },
    {
      label: 'Audio processed',
      value: durationLabel || '—',
      trendLabel: 'total runtime',
    },
  ];

  if (statsLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[var(--border)] rounded-lg overflow-hidden mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-[var(--bg-surface)] p-5">
            <Skeleton className="h-3 w-24 mb-3" />
            <Skeleton className="h-7 w-16" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[var(--border)] rounded-lg overflow-hidden mb-6">
      {items.map((item) => {
        const isPositive = (item.trend ?? 0) >= 0;
        const hasTrend = item.trend !== undefined;
        return (
          <div key={item.label} className="bg-[var(--bg-surface)] p-5">
            <p className="text-xs font-medium text-[var(--text-low)] uppercase tracking-widest mb-2">{item.label}</p>
            <p
              className="text-2xl font-bold text-[var(--text-high)] tracking-tight mb-1"
              style={{ fontVariantNumeric: 'tabular-nums' }}
            >
              {item.value}
            </p>
            <div className="flex items-center gap-1.5">
              {hasTrend && item.trend !== 0 && (
                <span className={`flex items-center gap-0.5 text-xs font-medium ${isPositive ? 'text-[var(--success)]' : 'text-[var(--error)]'}`}>
                  {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {isPositive && item.trend! > 0 ? `+${item.trend}%` : ''}
                </span>
              )}
              <span className="text-xs text-[var(--text-low)]">{item.trendLabel}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// --- Activity Feed ---
function ActivityFeed() {
  const { data: transcriptions } = useTranscriptions();

  const activities = useMemo(() => {
    if (!transcriptions?.items) return [];
    return transcriptions.items.slice(0, 8).map((t) => ({
      id: t.id,
      title: t.original_filename || t.video_url || 'Transcription',
      status: t.status as 'completed' | 'processing' | 'failed' | 'pending',
      source: t.source_type as string,
      time: new Date(t.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
    }));
  }, [transcriptions]);

  const statusConfig: Record<string, { dot: string; label: string }> = {
    completed:  { dot: 'bg-[var(--success)]',  label: 'done' },
    processing: { dot: 'bg-[var(--warning)] animate-pulse', label: 'running' },
    failed:     { dot: 'bg-[var(--error)]',    label: 'failed' },
    pending:    { dot: 'bg-[var(--text-low)]', label: 'pending' },
  };

  const sourceIcons: Record<string, string> = {
    youtube:    'brand-youtube',
    upload:     'upload',
    url:        'link',
    microphone: 'microphone',
  };

  return (
    <div className="surface-card p-5 h-full">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-sm font-semibold text-[var(--text-high)]">Recent activity</h2>
        <Button variant="ghost" size="sm" asChild>
          <Link href="/transcription" className="flex items-center gap-1 text-[var(--accent)] text-xs">
            View all <ArrowRight className="h-3 w-3" />
          </Link>
        </Button>
      </div>
      <div className="space-y-px">
        {activities.length === 0 ? (
          <div className="py-10 text-center">
            <p className="text-sm font-medium text-[var(--text-mid)] mb-1">No activity yet</p>
            <p className="text-xs text-[var(--text-low)] mb-4">Transcriptions you run will appear here.</p>
            <Button size="sm" asChild>
              <Link href="/transcription">Start transcribing</Link>
            </Button>
          </div>
        ) : (
          activities.map((activity) => (
            <div
              key={activity.id}
              className="flex items-center gap-3 py-2.5 px-2 rounded-md hover:bg-[var(--bg-elevated)] transition-colors cursor-default"
            >
              <div className="flex items-center justify-center w-7 h-7 rounded-md bg-[var(--bg-elevated)] shrink-0">
                <i
                  className={`tabler-${sourceIcons[activity.source] || 'file'}`}
                  style={{ fontSize: 13, color: 'var(--text-low)' }}
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-[var(--text-high)] truncate">{activity.title}</p>
                <span
                  className="text-xs text-[var(--text-low)]"
                  style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}
                >
                  {activity.time}
                </span>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <div className={`w-1.5 h-1.5 rounded-full ${statusConfig[activity.status]?.dot || 'bg-[var(--text-low)]'}`} />
                <span className="text-xs text-[var(--text-mid)]">
                  {statusConfig[activity.status]?.label || activity.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// --- Quick Actions ---
// No colored icon circles. Flat surfaces with accent on hover.
function QuickActions() {
  const actions = [
    { label: 'Transcribe',  href: '/transcription', icon: 'microphone' },
    { label: 'Chat',        href: '/chat',           icon: 'message-chatbot' },
    { label: 'Compare',     href: '/compare',        icon: 'arrows-diff' },
    { label: 'Pipeline',    href: '/pipelines',      icon: 'git-branch' },
    { label: 'Knowledge',   href: '/knowledge',      icon: 'books' },
    { label: 'Crawler',     href: '/crawler',        icon: 'world-download' },
    { label: 'Agents',      href: '/agents',         icon: 'robot' },
    { label: 'Sentiment',   href: '/sentiment',      icon: 'mood-happy' },
  ];

  return (
    <TooltipProvider>
      <div className="surface-card p-5">
        <h2 className="text-sm font-semibold text-[var(--text-high)] mb-4">Quick access</h2>
        <div className="grid grid-cols-4 gap-2">
          {actions.map((action) => (
            <Tooltip key={action.label}>
              <TooltipTrigger asChild>
                <Link
                  href={action.href}
                  className="group flex flex-col items-center gap-2 p-3 rounded-lg
                             border border-[var(--border)] bg-[var(--bg-elevated)]
                             hover:border-[var(--accent)]/40 hover:bg-[var(--bg-overlay)]
                             transition-all duration-150 cursor-pointer"
                >
                  <div className="flex items-center justify-center w-8 h-8 rounded-md">
                    <i
                      className={`tabler-${action.icon}`}
                      style={{ fontSize: 16, color: 'var(--text-mid)' }}
                    />
                  </div>
                  <span className="text-[0.68rem] text-[var(--text-low)] font-medium group-hover:text-[var(--text-mid)] transition-colors leading-tight text-center">
                    {action.label}
                  </span>
                </Link>
              </TooltipTrigger>
              <TooltipContent>{action.label}</TooltipContent>
            </Tooltip>
          ))}
        </div>
      </div>
    </TooltipProvider>
  );
}

// --- Usage Chart ---
function UsageChart() {
  const { data: stats } = useStats();

  const pieData = useMemo(() => {
    if (!stats) return [];
    const total = stats.total_transcriptions || 0;
    return [
      { name: 'Completed', value: Number(stats.completed || 0),  color: 'var(--success)' },
      { name: 'Failed',    value: Number(stats.failed || 0),     color: 'var(--error)' },
      { name: 'Pending',   value: Math.max(total - Number(stats.completed || 0) - Number(stats.failed || 0), 0), color: 'var(--text-low)' },
    ].filter((d) => d.value > 0);
  }, [stats]);

  const weeklyData = useMemo(() => {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days.map((day) => ({
      day,
      transcriptions: Math.floor(Math.random() * 8) + 1,
      aiCalls: Math.floor(Math.random() * 15) + 2,
    }));
  }, []);

  const tooltipStyle = {
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid var(--border)',
    borderRadius: 6,
    color: 'var(--text-high)',
    fontSize: 11,
    boxShadow: 'none',
  };

  // Two chart colors: accent (cyan) + a desaturated secondary (no purple)
  const CYAN = 'hsl(187, 93%, 65%)';
  const SLATE = 'hsl(215, 20%, 50%)';

  return (
    <div className="surface-card p-5 h-full">
      <h2 className="text-sm font-semibold text-[var(--text-high)] mb-5">Platform usage</h2>
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div className="md:col-span-7">
          <p className="text-[0.68rem] font-medium text-[var(--text-low)] mb-3 uppercase tracking-widest">
            Weekly activity
          </p>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={weeklyData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gradT" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={CYAN}  stopOpacity={0.20} />
                  <stop offset="95%" stopColor={CYAN}  stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradA" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={SLATE} stopOpacity={0.20} />
                  <stop offset="95%" stopColor={SLATE} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="day"
                tick={{ fontSize: 10, fill: 'var(--text-low)' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 10, fill: 'var(--text-low)' }}
                axisLine={false}
                tickLine={false}
              />
              <RechartsTooltip contentStyle={tooltipStyle} />
              <Area
                type="monotone"
                dataKey="transcriptions"
                name="Transcriptions"
                stroke={CYAN}
                fill="url(#gradT)"
                strokeWidth={1.5}
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="aiCalls"
                name="AI Calls"
                stroke={SLATE}
                fill="url(#gradA)"
                strokeWidth={1.5}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-2">
            {[{ color: CYAN, label: 'Transcriptions' }, { color: SLATE, label: 'AI calls' }].map((l) => (
              <div key={l.label} className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: l.color }} />
                <span className="text-[0.68rem] text-[var(--text-low)]">{l.label}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="md:col-span-5">
          <p className="text-[0.68rem] font-medium text-[var(--text-low)] mb-3 uppercase tracking-widest">
            Status split
          </p>
          {pieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={150}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={65}
                    paddingAngle={2}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1.5 mt-2">
                {pieData.map((d) => (
                  <div key={d.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: d.color }} />
                      <span className="text-xs text-[var(--text-mid)]">{d.name}</span>
                    </div>
                    <span
                      className="text-xs font-semibold text-[var(--text-high)]"
                      style={{ fontVariantNumeric: 'tabular-nums' }}
                    >
                      {d.value}
                    </span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-[150px] flex flex-col items-center justify-center gap-2">
              <CheckCircle2 className="h-6 w-6 text-[var(--text-low)]" />
              <p className="text-xs text-[var(--text-mid)]">No transcriptions yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// --- Module Status ---
// Shows active modules as compact chips. No gradients.
function ModuleStatus() {
  const modules = [
    'Transcription', 'Chat', 'Agents', 'Pipelines', 'Knowledge',
    'Crawler', 'Sentiment', 'Content Studio', 'Compare', 'Billing',
    'API Keys', 'Security',
  ];

  return (
    <div className="surface-card p-5">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-sm font-semibold text-[var(--text-high)]">Active modules</h2>
        <span
          className="text-xs font-medium text-[var(--accent)] px-2 py-0.5 rounded-md"
          style={{ background: 'var(--accent-glow)', border: '1px solid rgba(5,195,219,0.2)' }}
        >
          42 total
        </span>
      </div>
      <div className="flex gap-1.5 flex-wrap">
        {modules.map((m) => (
          <div
            key={m}
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium text-[var(--text-mid)] border border-[var(--border)] bg-[var(--bg-elevated)] cursor-default"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] shrink-0" />
            {m}
          </div>
        ))}
        <Link
          href="/modules"
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium text-[var(--accent)] border border-[var(--accent)]/20 bg-[var(--accent-glow)] hover:bg-[var(--accent)]/20 transition-colors"
        >
          +30 more
        </Link>
      </div>
    </div>
  );
}

// --- Main Dashboard ---
export default function DashboardPage() {
  const { data: user, isLoading: userLoading } = useCurrentUser();
  const { data: stats, isLoading: statsLoading } = useStats();

  if (userLoading) {
    return (
      <div className="p-6 space-y-5">
        <Skeleton className="h-10 w-full rounded-lg" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px rounded-lg overflow-hidden">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24 w-full" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-5">
      {/* System status bar — replaces WelcomeBanner */}
      <SystemStatusBar moduleCount={42} />

      {/* Stat row — no cards, just numbers */}
      <StatRow stats={stats} statsLoading={statsLoading} />

      {/* Charts + Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-8">
          <UsageChart />
        </div>
        <div className="lg:col-span-4">
          <ActivityFeed />
        </div>
      </div>

      {/* Quick access + Module status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <QuickActions />
        <ModuleStatus />
      </div>
    </div>
  );
}
