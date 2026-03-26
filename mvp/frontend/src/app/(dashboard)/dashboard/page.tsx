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

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/lib/design-hub/components/Button';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Avatar, AvatarFallback } from '@/lib/design-hub/components/Avatar';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';

import { useCurrentUser } from '@/features/auth/hooks/useAuth';
import { useTranscriptions } from '@/features/transcription/hooks/useTranscriptions';
import { useStats } from '@/features/transcription/hooks/useStats';

// --- Stat Card ---
function StatCard({
  title,
  value,
  subtitle,
  icon,
  color,
  trend,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: string;
  color: string;
  trend?: { value: number; label: string };
}) {
  return (
    <Card className="h-full relative overflow-visible">
      <CardContent className="p-6">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-sm text-[var(--text-mid)] mb-1 font-medium">
              {title}
            </p>
            <h4 className="text-3xl font-bold leading-tight text-[var(--text-high)]">
              {value}
            </h4>
            {subtitle && (
              <span className="text-xs text-[var(--text-mid)]">
                {subtitle}
              </span>
            )}
          </div>
          <Avatar className="w-12 h-12" style={{ backgroundColor: `${color}15` }}>
            <AvatarFallback className="bg-transparent" style={{ color }}>
              <i className={`tabler-${icon}`} style={{ fontSize: 24 }} />
            </AvatarFallback>
          </Avatar>
        </div>
        {trend && (
          <div className="flex items-center mt-2 gap-1">
            <Badge
              variant={trend.value >= 0 ? 'success' : 'destructive'}
              className="h-[22px] text-xs font-semibold"
            >
              {trend.value > 0 ? '+' : ''}{trend.value}%
            </Badge>
            <span className="text-xs text-[var(--text-mid)]">
              {trend.label}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// --- Welcome Banner ---
function WelcomeBanner({ userName, role }: { userName: string; role: string }) {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <Card className="mb-6 relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      <CardContent className="py-6 px-6 relative z-10">
        <h5 className="text-xl font-bold text-white mb-1">
          {greeting}, {userName}
        </h5>
        <p className="text-sm text-white/85 mb-4">
          Here&apos;s what&apos;s happening on your AI platform today
        </p>
        <div className="flex gap-2">
          <Badge className="bg-white/20 text-white border-none font-semibold">
            {role.toUpperCase()}
          </Badge>
        </div>
      </CardContent>
      {/* Decorative circles */}
      <div
        className="absolute rounded-full"
        style={{
          top: -40,
          right: -20,
          width: 160,
          height: 160,
          backgroundColor: 'rgba(255,255,255,0.08)',
        }}
      />
      <div
        className="absolute rounded-full"
        style={{
          bottom: -60,
          right: 60,
          width: 200,
          height: 200,
          backgroundColor: 'rgba(255,255,255,0.05)',
        }}
      />
    </Card>
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

  const statusVariants: Record<string, 'success' | 'warning' | 'destructive' | 'default' | 'outline'> = {
    completed: 'success',
    processing: 'warning',
    failed: 'destructive',
    pending: 'default',
  };

  const sourceIcons: Record<string, string> = {
    youtube: 'brand-youtube',
    upload: 'upload',
    url: 'link',
    microphone: 'microphone',
  };

  return (
    <Card className="h-full">
      <CardContent className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h6 className="text-base font-semibold text-[var(--text-high)]">Recent Activity</h6>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/transcription">View all</Link>
          </Button>
        </div>
        <div>
          {activities.length === 0 ? (
            <p className="text-sm text-[var(--text-mid)] py-4 text-center">
              No recent activity
            </p>
          ) : (
            activities.map((activity) => (
              <div key={activity.id} className="flex items-center gap-3 py-2 border-b border-[var(--border)] last:border-b-0">
                <Avatar className="w-9 h-9">
                  <AvatarFallback className="text-[var(--text-mid)]">
                    <i className={`tabler-${sourceIcons[activity.source] || 'file'}`} style={{ fontSize: 18 }} />
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--text-high)] truncate max-w-[200px]">
                    {activity.title}
                  </p>
                  <span className="text-xs text-[var(--text-mid)]">{activity.time}</span>
                </div>
                <Badge variant={statusVariants[activity.status] || 'outline'} className="shrink-0">
                  {activity.status}
                </Badge>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// --- Quick Actions ---
function QuickActions() {
  const actions = [
    { label: 'Transcribe', href: '/transcription', icon: 'microphone', color: '#667eea' },
    { label: 'Chat AI', href: '/chat', icon: 'message-chatbot', color: '#28c76f' },
    { label: 'Compare', href: '/compare', icon: 'arrows-diff', color: '#ff9f43' },
    { label: 'Pipeline', href: '/pipelines', icon: 'git-branch', color: '#ea5455' },
    { label: 'Knowledge', href: '/knowledge', icon: 'books', color: '#00cfe8' },
    { label: 'Crawler', href: '/crawler', icon: 'world-download', color: '#7367f0' },
    { label: 'Agents', href: '/agents', icon: 'robot', color: '#ff6b6b' },
    { label: 'Sentiment', href: '/sentiment', icon: 'mood-happy', color: '#ffd93d' },
  ];

  return (
    <TooltipProvider>
      <Card>
        <CardContent className="p-6">
          <h6 className="text-base font-semibold text-[var(--text-high)] mb-4">Quick Actions</h6>
          <div className="grid grid-cols-4 gap-3">
            {actions.map((action) => (
              <Tooltip key={action.label}>
                <TooltipTrigger asChild>
                  <Link
                    href={action.href}
                    className="flex flex-col items-center gap-1 p-3 rounded-lg w-full hover:bg-[var(--bg-elevated)] transition-colors"
                  >
                    <Avatar className="w-10 h-10" style={{ backgroundColor: `${action.color}15` }}>
                      <AvatarFallback className="bg-transparent" style={{ color: action.color }}>
                        <i className={`tabler-${action.icon}`} style={{ fontSize: 20 }} />
                      </AvatarFallback>
                    </Avatar>
                    <span className="text-xs text-[var(--text-mid)] font-medium truncate">
                      {action.label}
                    </span>
                  </Link>
                </TooltipTrigger>
                <TooltipContent>{action.label}</TooltipContent>
              </Tooltip>
            ))}
          </div>
        </CardContent>
      </Card>
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
      { name: 'Completed', value: Number(stats.completed || 0), color: '#28c76f' },
      { name: 'Failed', value: Number(stats.failed || 0), color: '#ea5455' },
      { name: 'Pending', value: Math.max(total - Number(stats.completed || 0) - Number(stats.failed || 0), 0), color: '#ff9f43' },
    ].filter((d) => d.value > 0);
  }, [stats]);

  // Simulated weekly data for area chart
  const weeklyData = useMemo(() => {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days.map((day) => ({
      day,
      transcriptions: Math.floor(Math.random() * 8) + 1,
      aiCalls: Math.floor(Math.random() * 15) + 2,
    }));
  }, []);

  return (
    <Card className="h-full">
      <CardContent className="p-6">
        <h6 className="text-base font-semibold text-[var(--text-high)] mb-4">Platform Usage</h6>
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          <div className="md:col-span-7">
            <p className="text-sm font-medium text-[var(--text-mid)] mb-2">
              Weekly Activity
            </p>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={weeklyData}>
                <defs>
                  <linearGradient id="colorTranscriptions" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#667eea" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#667eea" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorAiCalls" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#28c76f" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#28c76f" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="day" tick={{ fontSize: 12 }} stroke="var(--text-mid)" />
                <YAxis tick={{ fontSize: 12 }} stroke="var(--text-mid)" />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 8,
                  }}
                />
                <Area type="monotone" dataKey="transcriptions" stroke="#667eea" fill="url(#colorTranscriptions)" strokeWidth={2} />
                <Area type="monotone" dataKey="aiCalls" stroke="#28c76f" fill="url(#colorAiCalls)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="md:col-span-5">
            <p className="text-sm font-medium text-[var(--text-mid)] mb-2">
              Status Distribution
            </p>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={4} dataKey="value">
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[200px] flex items-center justify-center">
                <p className="text-sm text-[var(--text-mid)]">No data yet</p>
              </div>
            )}
            <div className="flex justify-center gap-4 mt-2">
              {pieData.map((d) => (
                <div key={d.name} className="flex items-center gap-1">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                  <span className="text-xs text-[var(--text-high)]">{d.name}: {d.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// --- Platform Stats Bar ---
function PlatformStatsBar() {
  const modules = [
    { name: 'Transcription', icon: 'microphone', status: 'active' },
    { name: 'Chat IA', icon: 'message-chatbot', status: 'active' },
    { name: 'Compare', icon: 'arrows-diff', status: 'active' },
    { name: 'Pipelines', icon: 'git-branch', status: 'active' },
    { name: 'Knowledge', icon: 'books', status: 'active' },
    { name: 'Agents', icon: 'robot', status: 'active' },
    { name: 'Crawler', icon: 'world-download', status: 'active' },
    { name: 'Sentiment', icon: 'mood-happy', status: 'active' },
    { name: 'Billing', icon: 'credit-card', status: 'active' },
    { name: 'API v1', icon: 'key', status: 'active' },
  ];

  return (
    <Card>
      <CardContent className="py-4 px-6">
        <div className="flex justify-between items-center mb-3">
          <p className="text-sm font-semibold text-[var(--text-high)]">Active Modules</p>
          <Badge variant="outline">{modules.length} modules</Badge>
        </div>
        <div className="flex gap-2 flex-wrap">
          {modules.map((m) => (
            <Badge key={m.name} variant="success" className="gap-1">
              <i className={`tabler-${m.icon}`} style={{ fontSize: 14 }} />
              {m.name}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// --- Main Dashboard ---
export default function DashboardPage() {
  const { data: user, isLoading: userLoading } = useCurrentUser();
  const { data: stats, isLoading: statsLoading } = useStats();

  if (userLoading || statsLoading) {
    return (
      <div className="p-6">
        <Skeleton className="h-[120px] mb-6 w-full" />
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-[120px] w-full" />
          ))}
        </div>
      </div>
    );
  }

  const userName = user?.full_name || user?.email?.split('@')[0] || 'User';
  const totalDuration = stats?.total_duration_seconds || 0;
  const hours = Math.floor(Number(totalDuration) / 3600);
  const minutes = Math.floor((Number(totalDuration) % 3600) / 60);

  return (
    <div className="p-6">
      {/* Welcome Banner */}
      <WelcomeBanner userName={userName} role={user?.role || 'user'} />

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 mb-6">
        <StatCard
          title="Total Transcriptions"
          value={stats?.total_transcriptions || 0}
          icon="file-text"
          color="#667eea"
          trend={{ value: 12, label: 'vs last month' }}
        />
        <StatCard
          title="Completed"
          value={stats?.completed || 0}
          subtitle={`${stats?.total_transcriptions ? Math.round((Number(stats.completed || 0) / Number(stats.total_transcriptions)) * 100) : 0}% success rate`}
          icon="circle-check"
          color="#28c76f"
        />
        <StatCard
          title="Failed"
          value={stats?.failed || 0}
          icon="alert-triangle"
          color="#ea5455"
        />
        <StatCard
          title="Audio Processed"
          value={hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`}
          icon="clock"
          color="#ff9f43"
        />
      </div>

      {/* Charts + Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
        <div className="lg:col-span-8">
          <UsageChart />
        </div>
        <div className="lg:col-span-4">
          <ActivityFeed />
        </div>
      </div>

      {/* Quick Actions + Modules */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <QuickActions />
        <PlatformStatsBar />
      </div>
    </div>
  );
}
