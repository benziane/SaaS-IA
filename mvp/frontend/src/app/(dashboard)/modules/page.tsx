/**
 * Platform Modules Page - Grade S++
 * Admin view of all registered backend modules and their status
 */

'use client';

import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Grid,
  Skeleton,
  Typography,
} from '@mui/material';
import { apiClient, extractErrorMessage } from '@/lib/apiClient';

/* ========================================================================
   TYPES
   ======================================================================== */

interface ModuleInfo {
  name: string;
  version: string;
  description: string;
  enabled: boolean;
  api_prefix: string;
  dependencies: string[];
}

/* ========================================================================
   LOADING SKELETON
   ======================================================================== */

function ModuleCardSkeleton(): JSX.Element {
  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title={<Skeleton variant="text" width="60%" />}
        subheader={<Skeleton variant="text" width="30%" />}
        action={<Skeleton variant="rounded" width={70} height={24} />}
      />
      <CardContent>
        <Skeleton variant="text" width="100%" />
        <Skeleton variant="text" width="80%" sx={{ mb: 2 }} />
        <Skeleton variant="text" width="40%" sx={{ mb: 1 }} />
        <Skeleton variant="text" width="50%" />
      </CardContent>
    </Card>
  );
}

/* ========================================================================
   MODULE CARD
   ======================================================================== */

function ModuleCard({ module }: { module: ModuleInfo }): JSX.Element {
  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardHeader
        title={module.name}
        subheader={`v${module.version}`}
        action={
          <Chip
            label={module.enabled ? 'Enabled' : 'Disabled'}
            color={module.enabled ? 'success' : 'default'}
            size="small"
            variant="outlined"
          />
        }
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
        subheaderTypographyProps={{ variant: 'caption' }}
      />
      <CardContent sx={{ flex: 1, pt: 0 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {module.description}
        </Typography>

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
          API Prefix
        </Typography>
        <Typography
          variant="body2"
          sx={{
            fontFamily: 'monospace',
            bgcolor: 'action.hover',
            px: 1,
            py: 0.5,
            borderRadius: 1,
            display: 'inline-block',
            mb: 2,
          }}
        >
          {module.api_prefix}
        </Typography>

        {module.dependencies.length > 0 && (
          <>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              Dependencies
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {module.dependencies.map((dep) => (
                <Chip key={dep} label={dep} size="small" variant="outlined" color="info" />
              ))}
            </Box>
          </>
        )}
      </CardContent>
    </Card>
  );
}

/* ========================================================================
   PAGE COMPONENT
   ======================================================================== */

export default function ModulesPage(): JSX.Element {
  const [modules, setModules] = useState<ModuleInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchModules(): Promise<void> {
      try {
        setLoading(true);
        setError(null);
        const response = await apiClient.get<ModuleInfo[]>('/api/modules');
        if (!cancelled) {
          setModules(response.data);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(extractErrorMessage(err));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchModules();

    return () => {
      cancelled = true;
    };
  }, []);

  /* ========================================================================
     RENDER
     ======================================================================== */

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Platform Modules
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Overview of all registered backend modules and their current status.
        </Typography>
      </Box>

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load modules: {error}
        </Alert>
      )}

      {/* Module Cards Grid */}
      <Grid container spacing={3}>
        {loading
          ? Array.from({ length: 3 }).map((_, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <ModuleCardSkeleton />
              </Grid>
            ))
          : modules.map((mod) => (
              <Grid item xs={12} sm={6} md={4} key={mod.name}>
                <ModuleCard module={mod} />
              </Grid>
            ))}
      </Grid>

      {/* Empty State */}
      {!loading && !error && modules.length === 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent sx={{ py: 6, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No modules registered
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Backend modules will appear here once they are registered with the platform.
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
