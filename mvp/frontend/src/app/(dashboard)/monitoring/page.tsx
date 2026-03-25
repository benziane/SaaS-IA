'use client';

import { useEffect, useState } from 'react';
import {
  Box, Card, CardContent, Chip, CircularProgress, FormControl, Grid,
  InputLabel, LinearProgress, MenuItem, Select, Skeleton, Typography,
} from '@mui/material';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import SpeedIcon from '@mui/icons-material/Speed';
import apiClient from '@/lib/apiClient';

interface DashboardData {
  period_days: number; total_calls: number; success_rate: number;
  total_tokens: number; total_cost_cents: number; total_cost_usd: number;
  avg_latency_ms: number; providers: Record<string, unknown>[];
  modules: Record<string, unknown>[]; recent_errors: Record<string, unknown>[];
  daily_trend: Record<string, unknown>[];
}

export default function MonitoringPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);

  useEffect(() => {
    setLoading(true);
    apiClient.get(`/api/monitoring/dashboard?days=${days}`)
      .then(res => setData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) return <Box sx={{ p: 3 }}><Skeleton variant="rectangular" height={400} /></Box>;
  if (!data) return <Box sx={{ p: 3 }}><Typography>No monitoring data available</Typography></Box>;

  const kpis = [
    { label: 'Total Calls', value: data.total_calls.toLocaleString(), color: 'primary.main' },
    { label: 'Success Rate', value: `${data.success_rate}%`, color: data.success_rate > 95 ? 'success.main' : 'warning.main' },
    { label: 'Total Tokens', value: data.total_tokens.toLocaleString(), color: 'info.main' },
    { label: 'Total Cost', value: `$${data.total_cost_usd.toFixed(4)}`, color: 'error.main' },
    { label: 'Avg Latency', value: `${data.avg_latency_ms}ms`, color: data.avg_latency_ms < 2000 ? 'success.main' : 'warning.main' },
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <MonitorHeartIcon color="primary" /> AI Monitoring
          </Typography>
          <Typography variant="body2" color="text.secondary">
            LLM observability - calls, latency, cost, providers, errors
          </Typography>
        </Box>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Period</InputLabel>
          <Select value={days} label="Period" onChange={(e) => setDays(Number(e.target.value))}>
            <MenuItem value={1}>24h</MenuItem>
            <MenuItem value={7}>7 days</MenuItem>
            <MenuItem value={30}>30 days</MenuItem>
            <MenuItem value={90}>90 days</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* KPI Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {kpis.map((kpi) => (
          <Grid item xs={6} sm={2.4} key={kpi.label}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 2, '&:last-child': { pb: 2 } }}>
                <Typography variant="h4" sx={{ color: kpi.color, fontWeight: 'bold' }}>{kpi.value}</Typography>
                <Typography variant="caption" color="text.secondary">{kpi.label}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Provider Comparison */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <SpeedIcon /> Provider Performance
              </Typography>
              {data.providers.map((p: Record<string, unknown>) => (
                <Box key={p.provider as string} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Chip label={p.provider as string} size="small" color="primary" />
                      <Chip label={`${p.calls} calls`} size="small" variant="outlined" />
                      <Chip label={`${p.avg_latency_ms}ms`} size="small" variant="outlined" />
                    </Box>
                    <Typography variant="caption">{(p.success_rate as number)}% success</Typography>
                  </Box>
                  <LinearProgress variant="determinate" value={p.success_rate as number}
                    color={(p.success_rate as number) > 95 ? 'success' : 'warning'} />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Module Usage */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Module Usage</Typography>
              {data.modules.map((m: Record<string, unknown>) => (
                <Box key={m.module as string} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                  <Chip label={m.module as string} size="small" variant="outlined" />
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Typography variant="body2">{(m.calls as number)} calls</Typography>
                    <Typography variant="caption" color="text.secondary">${((m.cost_cents as number) / 100).toFixed(4)}</Typography>
                  </Box>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Errors */}
        {data.recent_errors.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }} color="error">Recent Errors</Typography>
                {data.recent_errors.map((e: Record<string, unknown>, i: number) => (
                  <Box key={i} sx={{ mb: 1, pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                    <Box sx={{ display: 'flex', gap: 0.5, mb: 0.5 }}>
                      <Chip label={e.provider as string} size="small" color="error" variant="outlined" />
                      <Chip label={e.module as string} size="small" variant="outlined" />
                      <Chip label={e.action as string} size="small" variant="outlined" />
                    </Box>
                    <Typography variant="caption" color="error">{e.error as string}</Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
}
