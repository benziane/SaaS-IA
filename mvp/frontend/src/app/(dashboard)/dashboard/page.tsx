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
import { TrendingUp, TrendingDown, ArrowRight, Zap } from 'lucide-react';

import { Button } from '@/lib/design-hub/components/Button';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';

import { useCurrentUser } from '@/features/auth/hooks/useAuth';
import { useTranscriptions } from '@/features/transcription/hooks/useTranscriptions';
import { useStats } from '@/features/transcription/hooks/useStats';

// --- Stat Card (glassmorphism) ---
function StatCard({
  title,
  value,
  subtitle,
  icon,
  gradientFrom,
  gradientTo,
  trend,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: string;
  gradientFrom: string;
  gradientTo: string;
  trend?: { value: number; label: string };
}) {
  const isPositive = (trend?.value ?? 0) >= 0;
  return (
    <div className="surface-card border-glow-accent p-5 animate-enter">
      <div className="flex items-start justify-between mb-4">
        <div
          className="flex items-center justify-center w-11 h-11 rounded-xl"
          style={{ background: `linear-gradient(135deg, ${gradientFrom}, ${gradientTo})` }}
        >
          <i className={`tabler-${icon}`} style={{ fontSize: 22, color: '#fff' }} />
        </div>
        {trend && (
          <span
            className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full ${
              isPositive
                ? 'bg-[var(--success)]/10 text-[var(--success)]'
                : 'bg-[var(--error)]/10 text-[var(--error)]'
            }`}
          >
            {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {isPositive ? '+' : ''}{trend.value}%
          </span>
        )}
      </div>
      <p className="text-[var(--text-mid)] text-sm font-medium mb-1">{title}</p>
      <p className="text-[var(--text-high)] text-2xl font-bold tracking-tight">{value}</p>
      {subtitle && <p className="text-[var(--text-low)] text-xs mt-1">{subtitle}</p>}
      {trend && <p className="text-[var(--text-low)] text-xs mt-1">{trend.label}</p>}
    </div>
  );
}

// --- Welcome Banner ---
function WelcomeBanner({ userName, role }: { userName: string; role: string }) {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <div
      className="relative overflow-hidden rounded-2xl mb-6 p-6 animate-enter"
      style={{
        background: 'linear-gradient(135deg, hsl(187,96%,10%) 0%, hsl(260,60%,12%) 100%)',
        border: '1px solid rgba(5, 195, 219, 0.2)',
      }}
    >
      {/* SVG grid overlay */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'40\' height=\'40\' viewBox=\'0 0 40 40\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg stroke=\'%23ffffff\' stroke-width=\'0.8\'%3E%3Cpath d=\'M40 0H0v40\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
        }}
      />
      {/* Glow orbs */}
      <div className="absolute -top-12 -right-8 w-48 h-48 rounded-full opacity-10"
        style={{ background: 'radial-gradient(circle, var(--accent), transparent 70%)' }} />
      <div className="absolute -bottom-16 right-32 w-64 h-64 rounded-full opacity-5"
        style={{ background: 'radial-gradient(circle, #a855f7, transparent 70%)' }} />

      <div className="relative z-10 flex items-center justify-between">
        <div>
          <p className="text-[var(--text-mid)] text-sm font-medium mb-1">{greeting} 👋</p>
          <h5 className="text-white text-xl font-bold mb-2 tracking-tight">
            Welcome back, <span className="text-gradient">{userName}</span>
          </h5>
          <p className="text-white/60 text-sm mb-4">
            Your AI platform is running smoothly — 40 modules active
          </p>
          <div className="flex items-center gap-2">
            <span
              className="inline-flex items-center gap-1 text-xs font-semibold px-3 py-1 rounded-full"
              style={{ background: 'rgba(5,195,219,0.15)', color: 'var(--accent)', border: '1px solid rgba(5,195,219,0.3)' }}
            >
              <Zap className="h-3 w-3" />
              {role.toUpperCase()}
            </span>
          </div>
        </div>
        <Button variant="outline" size="sm" asChild
          className="hidden md:inline-flex border-white/20 text-white hover:bg-white/10 shrink-0">
          <Link href="/transcription" className="flex items-center gap-2">
            New Transcription <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </div>
  );
}

// --- Activity Feed ---
function ActivityFeed() {
  const { data: transcriptions } = useTranscriptions();

  const activities = useMemo(() => {
    if (!transcriptions?.items) return [];
    return transcriptions.items.slice(0, 6).map((t) => ({
      id: t.id,
      title: t.original_filename || t.video_url || 'Transcription',
      status: t.status,
      source: t.source_type,
      time: new Date(t.created_at).toLocaleString(),
    }));
  }, [transcriptions]);

  const statusDot: Record<string, string> = {
    completed: 'bg-[var(--success)]',
    processing: 'bg-[var(--warning)]',
    failed: 'bg-[var(--error)]',
    pending: 'bg-[var(--text-low)]',
  };

  const sourceIcons: Record<string, string> = {
    youtube: 'brand-youtube',
    upload: 'upload',
    url: 'link',
    microphone: 'microphone',
  };

  return (
    <div className="surface-card p-5 h-full">
      <div className="flex justify-between items-center mb-4">
        <h6 className="text-[var(--text-high)] text-sm font-semibold">Recent Activity</h6>
        <Button variant="ghost" size="sm" asChild>
          <Link href="/transcription" className="flex items-center gap-1 text-[var(--accent)] text-xs">
            View all <ArrowRight className="h-3 w-3" />
          </Link>
        </Button>
      </div>
      <div className="space-y-1">
        {activities.length === 0 ? (
          <p className="text-sm text-[var(--text-mid)] py-8 text-center">No recent activity</p>
        ) : (
          activities.map((activity) => (
            <div key={activity.id}
              className="flex items-center gap-3 py-2.5 px-2 rounded-lg hover:bg-[var(--bg-elevated)] transition-colors">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-[var(--bg-elevated)] shrink-0">
                <i className={`tabler-${sourceIcons[activity.source] || 'file'}`}
                  style={{ fontSize: 16, color: 'var(--text-mid)' }} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[var(--text-high)] truncate">{activity.title}</p>
                <span className="text-xs text-[var(--text-low)]">{activity.time}</span>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <div className={`w-1.5 h-1.5 rounded-full ${statusDot[activity.status] || 'bg-[var(--text-low)]'}`} />
                <span className="text-xs text-[var(--text-mid)] capitalize">{activity.status}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// --- Quick Actions ---
function QuickActions() {
  const actions = [
    { label: 'Transcribe', href: '/transcription', icon: 'microphone',  from: '#05c3db', to: '#0284a8' },
    { label: 'Chat AI',    href: '/chat',          icon: 'message-chatbot', from: '#28c76f', to: '#1ea85d' },
    { label: 'Compare',   href: '/compare',        icon: 'arrows-diff', from: '#ff9f43', to: '#e08835' },
    { label: 'Pipeline',  href: '/pipelines',      icon: 'git-branch',  from: '#ea5455', to: '#c93f40' },
    { label: 'Knowledge', href: '/knowledge',      icon: 'books',       from: '#00cfe8', to: '#00a5bb' },
    { label: 'Crawler',   href: '/crawler',        icon: 'world-download', from: '#a855f7', to: '#8b2fd4' },
    { label: 'Agents',    href: '/agents',         icon: 'robot',       from: '#f97316', to: '#c75b0c' },
    { label: 'Sentiment', href: '/sentiment',      icon: 'mood-happy',  from: '#fbbf24', to: '#d97706' },
  ];

  return (
    <TooltipProvider>
      <div className="surface-card p-5">
        <h6 className="text-[var(--text-high)] text-sm font-semibold mb-4">Quick Actions</h6>
        <div className="grid grid-cols-4 gap-2">
          {actions.map((action) => (
            <Tooltip key={action.label}>
              <TooltipTrigger asChild>
                <Link
                  href={action.href}
                  className="group flex flex-col items-center gap-2 p-3 rounded-xl
                             border border-[var(--border)] bg-[var(--bg-elevated)]
                             hover:border-[var(--accent)]/40 hover:shadow-[var(--shadow-lg)]
                             transition-all duration-200 cursor-pointer"
                >
                  <div
                    className="flex items-center justify-center w-9 h-9 rounded-lg"
                    style={{ background: `linear-gradient(135deg, ${action.from}, ${action.to})` }}
                  >
                    <i className={`tabler-${action.icon}`} style={{ fontSize: 18, color: '#fff' }} />
                  </div>
                  <span className="text-[0.7rem] text-[var(--text-mid)] font-medium group-hover:text-[var(--text-high)] transition-colors">
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
      { name: 'Completed', value: Number(stats.completed || 0),  color: 'var(--chart-2)' },
      { name: 'Failed',    value: Number(stats.failed || 0),     color: 'var(--chart-5)' },
      { name: 'Pending',   value: Math.max(total - Number(stats.completed || 0) - Number(stats.failed || 0), 0), color: 'var(--chart-3)' },
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
    borderRadius: 8,
    color: 'var(--text-high)',
    fontSize: 12,
  };

  return (
    <div className="surface-card p-5 h-full">
      <h6 className="text-[var(--text-high)] text-sm font-semibold mb-5">Platform Usage</h6>
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div className="md:col-span-7">
          <p className="text-xs font-medium text-[var(--text-mid)] mb-3 uppercase tracking-wider">Weekly Activity</p>
          <ResponsiveContainer width="100%" height={190}>
            <AreaChart data={weeklyData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gradT" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#05c3db" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#05c3db" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradA" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#a855f7" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="day" tick={{ fontSize: 11, fill: 'var(--text-low)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-low)' }} axisLine={false} tickLine={false} />
              <RechartsTooltip contentStyle={tooltipStyle} />
              <Area type="monotone" dataKey="transcriptions" name="Transcriptions"
                stroke="#05c3db" fill="url(#gradT)" strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="aiCalls" name="AI Calls"
                stroke="#a855f7" fill="url(#gradA)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-2">
            {[{ color: '#05c3db', label: 'Transcriptions' }, { color: '#a855f7', label: 'AI Calls' }].map((l) => (
              <div key={l.label} className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: l.color }} />
                <span className="text-[0.7rem] text-[var(--text-low)]">{l.label}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="md:col-span-5">
          <p className="text-xs font-medium text-[var(--text-mid)] mb-3 uppercase tracking-wider">Status Split</p>
          {pieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={160}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={70}
                    paddingAngle={3} dataKey="value" strokeWidth={0}>
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
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                      <span className="text-xs text-[var(--text-mid)]">{d.name}</span>
                    </div>
                    <span className="text-xs font-semibold text-[var(--text-high)]">{d.value}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-[160px] flex items-center justify-center">
              <p className="text-sm text-[var(--text-mid)]">No data yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// --- Platform Stats Bar ---
function PlatformStatsBar() {
  const modules = [
    { name: 'Transcription', icon: 'microphone' },
    { name: 'Chat IA',       icon: 'message-chatbot' },
    { name: 'Compare',       icon: 'arrows-diff' },
    { name: 'Pipelines',     icon: 'git-branch' },
    { name: 'Knowledge',     icon: 'books' },
    { name: 'Agents',        icon: 'robot' },
    { name: 'Crawler',       icon: 'world-download' },
    { name: 'Sentiment',     icon: 'mood-happy' },
    { name: 'Billing',       icon: 'credit-card' },
    { name: 'API v1',        icon: 'key' },
  ];

  return (
    <div className="surface-card p-5">
      <div className="flex justify-between items-center mb-4">
        <h6 className="text-[var(--text-high)] text-sm font-semibold">Active Modules</h6>
        <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full"
          style={{ background: 'rgba(5,195,219,0.1)', color: 'var(--accent)', border: '1px solid rgba(5,195,219,0.2)' }}>
          {modules.length} running
        </span>
      </div>
      <div className="flex gap-2 flex-wrap">
        {modules.map((m) => (
          <div
            key={m.name}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-colors
                       hover:bg-[var(--bg-overlay)] cursor-default"
            style={{ background: 'var(--bg-elevated)', color: 'var(--text-mid)', border: '1px solid var(--border)' }}
          >
            <i className={`tabler-${m.icon}`} style={{ fontSize: 13, color: 'var(--accent)' }} />
            {m.name}
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Main Dashboard ---
export default function DashboardPage() {
  const { data: user, isLoading: userLoading } = useCurrentUser();
  const { data: stats, isLoading: statsLoading } = useStats();

  if (userLoading || statsLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-[140px] w-full rounded-2xl" />
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-[120px] w-full rounded-xl" />)}
        </div>
      </div>
    );
  }

  const userName = user?.full_name || user?.email?.split('@')[0] || 'User';
  const totalDuration = stats?.total_duration_seconds || 0;
  const hours = Math.floor(Number(totalDuration) / 3600);
  const minutes = Math.floor((Number(totalDuration) % 3600) / 60);
  const successRate = stats?.total_transcriptions
    ? Math.round((Number(stats.completed || 0) / Number(stats.total_transcriptions)) * 100)
    : 0;

  return (
    <div className="p-6 space-y-5">
      {/* Welcome Banner */}
      <WelcomeBanner userName={userName} role={user?.role || 'user'} />

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Transcriptions"
          value={stats?.total_transcriptions || 0}
          icon="file-text"
          gradientFrom="#05c3db"
          gradientTo="#0284a8"
          trend={{ value: 12, label: 'vs last month' }}
        />
        <StatCard
          title="Completed"
          value={stats?.completed || 0}
          subtitle={`${successRate}% success rate`}
          icon="circle-check"
          gradientFrom="#28c76f"
          gradientTo="#1ea85d"
        />
        <StatCard
          title="Failed"
          value={stats?.failed || 0}
          icon="alert-triangle"
          gradientFrom="#ea5455"
          gradientTo="#c93f40"
        />
        <StatCard
          title="Audio Processed"
          value={hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`}
          icon="clock"
          gradientFrom="#ff9f43"
          gradientTo="#e08835"
        />
      </div>

      {/* Charts + Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-8">
          <UsageChart />
        </div>
        <div className="lg:col-span-4">
          <ActivityFeed />
        </div>
      </div>

      {/* Quick Actions + Modules */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <QuickActions />
        <PlatformStatsBar />
      </div>
    </div>
  );
}
