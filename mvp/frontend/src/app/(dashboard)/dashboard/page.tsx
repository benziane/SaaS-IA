/**
 * Dashboard Page - Grade S++
 * Main dashboard with real transcription statistics from the backend
 */

'use client';

import {
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemText,
  Skeleton,
  Typography,
} from '@mui/material';
import {
  AccessTime,
  CheckCircle,
  Error as ErrorIcon,
  Transcribe,
} from '@mui/icons-material';
import { useCurrentUser } from '@/features/auth/hooks';
import { useStats } from '@/features/transcription/hooks';
import type { TranscriptionStats, RecentTranscription } from '@/features/transcription/types';
import { TranscriptionStatus } from '@/features/transcription/types';

/* ========================================================================
   HELPERS
   ======================================================================== */

function formatDuration(totalSeconds: number): string {
  if (totalSeconds === 0) return '0 min';
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  if (hours > 0) {
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
  }
  return `${minutes} min`;
}

function getStatusColor(
  status: TranscriptionStatus
): 'success' | 'error' | 'warning' | 'info' | 'default' {
  switch (status) {
    case TranscriptionStatus.COMPLETED:
      return 'success';
    case TranscriptionStatus.FAILED:
      return 'error';
    case TranscriptionStatus.PROCESSING:
      return 'warning';
    case TranscriptionStatus.PENDING:
      return 'info';
    default:
      return 'default';
  }
}

function getStatusLabel(status: TranscriptionStatus): string {
  switch (status) {
    case TranscriptionStatus.COMPLETED:
      return 'Completed';
    case TranscriptionStatus.FAILED:
      return 'Failed';
    case TranscriptionStatus.PROCESSING:
      return 'Processing';
    case TranscriptionStatus.PENDING:
      return 'Pending';
    default:
      return status;
  }
}

function extractVideoTitle(url: string): string {
  try {
    const parsed = new URL(url);
    const videoId =
      parsed.searchParams.get('v') ??
      parsed.pathname.split('/').pop() ??
      url;
    return videoId;
  } catch {
    return url;
  }
}

/* ========================================================================
   TYPES
   ======================================================================== */

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: 'primary' | 'success' | 'warning' | 'error';
  loading?: boolean;
}

/* ========================================================================
   COMPONENTS
   ======================================================================== */

function StatCard({ title, value, icon, color, loading = false }: StatCardProps): JSX.Element {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 48,
              height: 48,
              borderRadius: 2,
              bgcolor: `${color}.main`,
              color: `${color}.contrastText`,
              mr: 2,
            }}
            aria-hidden="true"
          >
            {icon}
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            {loading ? (
              <Skeleton variant="text" width={60} height={40} />
            ) : (
              <Typography variant="h4" component="div" sx={{ fontWeight: 600 }}>
                {value}
              </Typography>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

function RecentTranscriptionsList({
  items,
  loading,
}: {
  items: RecentTranscription[];
  loading: boolean;
}): JSX.Element {
  if (loading) {
    return (
      <List disablePadding>
        {Array.from({ length: 3 }).map((_, i) => (
          <ListItem key={i} divider={i < 2}>
            <ListItemText
              primary={<Skeleton variant="text" width="60%" />}
              secondary={<Skeleton variant="text" width="30%" />}
            />
          </ListItem>
        ))}
      </List>
    );
  }

  if (items.length === 0) {
    return (
      <Box sx={{ py: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          No transcriptions yet. Start by creating your first one.
        </Typography>
        <Box
          component="a"
          href="/transcription"
          sx={{
            display: 'inline-block',
            mt: 2,
            color: 'primary.main',
            textDecoration: 'none',
            fontWeight: 500,
            '&:hover': { textDecoration: 'underline' },
          }}
        >
          Go to Transcriptions
        </Box>
      </Box>
    );
  }

  return (
    <List disablePadding>
      {items.map((item, index) => (
        <ListItem key={item.id} divider={index < items.length - 1}>
          <ListItemText
            primary={extractVideoTitle(item.video_url)}
            secondary={new Date(item.created_at).toLocaleString()}
            primaryTypographyProps={{
              noWrap: true,
              sx: { maxWidth: '70%' },
            }}
          />
          <Chip
            label={getStatusLabel(item.status)}
            color={getStatusColor(item.status)}
            size="small"
            variant="outlined"
          />
        </ListItem>
      ))}
    </List>
  );
}

/* ========================================================================
   PAGE COMPONENT
   ======================================================================== */

export default function DashboardPage(): JSX.Element {
  const { data: user } = useCurrentUser();
  const { data: stats, isLoading, isError } = useStats();

  const safeStats: TranscriptionStats = stats ?? {
    total_transcriptions: 0,
    completed: 0,
    failed: 0,
    pending: 0,
    processing: 0,
    total_duration_seconds: 0,
    avg_confidence: null,
    recent_transcriptions: [],
  };

  /* ========================================================================
     RENDER
     ======================================================================== */

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Welcome back{user ? `, ${user.email.split('@')[0]}` : ''}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here is an overview of your transcription activity.
        </Typography>
      </Box>

      {/* Error Banner */}
      {isError && (
        <Card sx={{ mb: 3, bgcolor: 'error.light' }}>
          <CardContent sx={{ py: 1.5 }}>
            <Typography variant="body2" color="error.dark">
              Failed to load statistics. Please try again later.
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Transcriptions"
            value={safeStats.total_transcriptions}
            icon={<Transcribe />}
            color="primary"
            loading={isLoading}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Completed"
            value={safeStats.completed}
            icon={<CheckCircle />}
            color="success"
            loading={isLoading}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Failed"
            value={safeStats.failed}
            icon={<ErrorIcon />}
            color="error"
            loading={isLoading}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Duration"
            value={formatDuration(safeStats.total_duration_seconds)}
            icon={<AccessTime />}
            color="warning"
            loading={isLoading}
          />
        </Grid>
      </Grid>

      {/* Bottom Row */}
      <Grid container spacing={3}>
        {/* Recent Transcriptions */}
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Recent Transcriptions
              </Typography>
              <RecentTranscriptionsList
                items={safeStats.recent_transcriptions}
                loading={isLoading}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions and Account Info */}
        <Grid item xs={12} md={5}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Quick Start
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Get started with your first transcription
              </Typography>
              <Box
                component="a"
                href="/transcription"
                sx={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  color: 'primary.main',
                  textDecoration: 'none',
                  fontWeight: 500,
                  '&:hover': { textDecoration: 'underline' },
                }}
              >
                Go to Transcriptions
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Account Info
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                <strong>Email:</strong> {user?.email || 'Loading...'}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                <strong>Role:</strong> {user?.role || 'Loading...'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                <strong>Status:</strong>{' '}
                {user?.is_active ? (
                  <span style={{ color: 'green' }}>Active</span>
                ) : (
                  <span style={{ color: 'red' }}>Inactive</span>
                )}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
