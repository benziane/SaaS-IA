/**
 * Dashboard Page - Grade S++
 * Main dashboard with statistics and widgets
 */

'use client';

import {
  Box,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Typography,
} from '@mui/material';
import {
  CheckCircle,
  Error,
  HourglassEmpty,
  Transcribe,
} from '@mui/icons-material';
import { useCurrentUser } from '@/features/auth/hooks';

/* ========================================================================
   TYPES
   ======================================================================== */

interface StatCardProps {
  title: string;
  value: number;
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
              <LinearProgress sx={{ mt: 1 }} />
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

/* ========================================================================
   PAGE COMPONENT
   ======================================================================== */

export default function DashboardPage(): JSX.Element {
  const { data: user, isLoading } = useCurrentUser();
  
  /* Mock data - Will be replaced with real API calls */
  const stats = {
    total: 0,
    completed: 0,
    processing: 0,
    failed: 0,
  };
  
  /* ========================================================================
     RENDER
     ======================================================================== */
  
  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Welcome back{user ? `, ${user.email.split('@')[0]}` : ''}! 👋
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here&apos;s what&apos;s happening with your AI services today.
        </Typography>
      </Box>
      
      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Transcriptions"
            value={stats.total}
            icon={<Transcribe />}
            color="primary"
            loading={isLoading}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Completed"
            value={stats.completed}
            icon={<CheckCircle />}
            color="success"
            loading={isLoading}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Processing"
            value={stats.processing}
            icon={<HourglassEmpty />}
            color="warning"
            loading={isLoading}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Failed"
            value={stats.failed}
            icon={<Error />}
            color="error"
            loading={isLoading}
          />
        </Grid>
      </Grid>
      
      {/* Quick Actions */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
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
                  '&:hover': {
                    textDecoration: 'underline',
                  },
                }}
              >
                Go to Transcriptions →
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
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

