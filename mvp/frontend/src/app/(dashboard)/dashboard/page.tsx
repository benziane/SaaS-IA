'use client';

import { useMemo } from 'react';
import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Skeleton,
  Tooltip,
  Typography,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
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
    <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
      <CardContent sx={{ pb: '16px !important' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5, fontWeight: 500 }}>
              {title}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Avatar
            sx={{
              bgcolor: `${color}15`,
              color: color,
              width: 48,
              height: 48,
            }}
          >
            <i className={`tabler-${icon}`} style={{ fontSize: 24 }} />
          </Avatar>
        </Box>
        {trend && (
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, gap: 0.5 }}>
            <Chip
              label={`${trend.value > 0 ? '+' : ''}${trend.value}%`}
              size="small"
              color={trend.value >= 0 ? 'success' : 'error'}
              sx={{ height: 22, fontSize: '0.75rem', fontWeight: 600 }}
            />
            <Typography variant="caption" color="text.secondary">
              {trend.label}
            </Typography>
          </Box>
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
    <Card
      sx={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        mb: 3,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <CardContent sx={{ py: 3, position: 'relative', zIndex: 1 }}>
        <Typography variant="h5" sx={{ fontWeight: 700, mb: 0.5 }}>
          {greeting}, {userName}
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.85, mb: 2 }}>
          Here&apos;s what&apos;s happening on your AI platform today
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip label={role.toUpperCase()} size="small" sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 600 }} />
        </Box>
      </CardContent>
      {/* Decorative circles */}
      <Box
        sx={{
          position: 'absolute',
          top: -40,
          right: -20,
          width: 160,
          height: 160,
          borderRadius: '50%',
          bgcolor: 'rgba(255,255,255,0.08)',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: -60,
          right: 60,
          width: 200,
          height: 200,
          borderRadius: '50%',
          bgcolor: 'rgba(255,255,255,0.05)',
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

  const statusColors: Record<string, 'success' | 'warning' | 'error' | 'info' | 'default'> = {
    completed: 'success',
    processing: 'warning',
    failed: 'error',
    pending: 'info',
  };

  const sourceIcons: Record<string, string> = {
    youtube: 'brand-youtube',
    upload: 'upload',
    url: 'link',
    microphone: 'microphone',
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>Recent Activity</Typography>
          <Button size="small" href="/transcription">View all</Button>
        </Box>
        <List disablePadding>
          {activities.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
              No recent activity
            </Typography>
          ) : (
            activities.map((activity) => (
              <ListItem key={activity.id} sx={{ px: 0, py: 1 }} divider>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: 'action.hover', width: 36, height: 36 }}>
                    <i className={`tabler-${sourceIcons[activity.source] || 'file'}`} style={{ fontSize: 18 }} />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Typography variant="body2" noWrap sx={{ maxWidth: 200, fontWeight: 500 }}>
                      {activity.title}
                    </Typography>
                  }
                  secondary={activity.time}
                  secondaryTypographyProps={{ variant: 'caption' }}
                />
                <Chip label={activity.status} size="small" color={statusColors[activity.status] || 'default'} variant="outlined" />
              </ListItem>
            ))
          )}
        </List>
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
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Quick Actions</Typography>
        <Grid container spacing={1.5}>
          {actions.map((action) => (
            <Grid item xs={3} key={action.label}>
              <Tooltip title={action.label}>
                <Button
                  href={action.href}
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: 0.5,
                    p: 1.5,
                    borderRadius: 2,
                    width: '100%',
                    minWidth: 0,
                    '&:hover': { bgcolor: `${action.color}10` },
                  }}
                >
                  <Avatar sx={{ bgcolor: `${action.color}15`, color: action.color, width: 40, height: 40 }}>
                    <i className={`tabler-${action.icon}`} style={{ fontSize: 20 }} />
                  </Avatar>
                  <Typography variant="caption" color="text.secondary" noWrap sx={{ fontWeight: 500 }}>
                    {action.label}
                  </Typography>
                </Button>
              </Tooltip>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
}

// --- Usage Chart ---
function UsageChart() {
  const theme = useTheme();
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
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Platform Usage</Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={7}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
              Weekly Activity
            </Typography>
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
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                <XAxis dataKey="day" tick={{ fontSize: 12 }} stroke={theme.palette.text.secondary} />
                <YAxis tick={{ fontSize: 12 }} stroke={theme.palette.text.secondary} />
                <RechartsTooltip
                  contentStyle={{
                    backgroundColor: theme.palette.background.paper,
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: 8,
                  }}
                />
                <Area type="monotone" dataKey="transcriptions" stroke="#667eea" fill="url(#colorTranscriptions)" strokeWidth={2} />
                <Area type="monotone" dataKey="aiCalls" stroke="#28c76f" fill="url(#colorAiCalls)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </Grid>
          <Grid item xs={12} md={5}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
              Status Distribution
            </Typography>
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
              <Box sx={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography variant="body2" color="text.secondary">No data yet</Typography>
              </Box>
            )}
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 1 }}>
              {pieData.map((d) => (
                <Box key={d.name} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: d.color }} />
                  <Typography variant="caption">{d.name}: {d.value}</Typography>
                </Box>
              ))}
            </Box>
          </Grid>
        </Grid>
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
      <CardContent sx={{ py: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Active Modules</Typography>
          <Chip label={`${modules.length} modules`} size="small" color="primary" variant="outlined" />
        </Box>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {modules.map((m) => (
            <Chip
              key={m.name}
              icon={<i className={`tabler-${m.icon}`} style={{ fontSize: 14 }} />}
              label={m.name}
              size="small"
              variant="outlined"
              color="success"
              sx={{ fontSize: '0.75rem' }}
            />
          ))}
        </Box>
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
      <Box sx={{ p: 3 }}>
        <Skeleton variant="rounded" height={120} sx={{ mb: 3 }} />
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map((i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <Skeleton variant="rounded" height={120} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  const userName = user?.full_name || user?.email?.split('@')[0] || 'User';
  const totalDuration = stats?.total_duration_seconds || 0;
  const hours = Math.floor(Number(totalDuration) / 3600);
  const minutes = Math.floor((Number(totalDuration) % 3600) / 60);

  return (
    <Box sx={{ p: 3 }}>
      {/* Welcome Banner */}
      <WelcomeBanner userName={userName} role={user?.role || 'user'} />

      {/* Stat Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Transcriptions"
            value={stats?.total_transcriptions || 0}
            icon="file-text"
            color="#667eea"
            trend={{ value: 12, label: 'vs last month' }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Completed"
            value={stats?.completed || 0}
            subtitle={`${stats?.total_transcriptions ? Math.round((Number(stats.completed || 0) / Number(stats.total_transcriptions)) * 100) : 0}% success rate`}
            icon="circle-check"
            color="#28c76f"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Failed"
            value={stats?.failed || 0}
            icon="alert-triangle"
            color="#ea5455"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Audio Processed"
            value={hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`}
            icon="clock"
            color="#ff9f43"
          />
        </Grid>
      </Grid>

      {/* Charts + Activity */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} lg={8}>
          <UsageChart />
        </Grid>
        <Grid item xs={12} lg={4}>
          <ActivityFeed />
        </Grid>
      </Grid>

      {/* Quick Actions + Modules */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <QuickActions />
        </Grid>
        <Grid item xs={12} md={6}>
          <PlatformStatsBar />
        </Grid>
      </Grid>
    </Box>
  );
}
