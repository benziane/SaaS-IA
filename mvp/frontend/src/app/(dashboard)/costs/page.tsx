'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  MenuItem,
  Select,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';

import { useCostDashboard, useCostAlerts } from '@/features/cost-tracker/hooks/useCosts';
import { getExportUrl } from '@/features/cost-tracker/api';
import type { CostAlert } from '@/features/cost-tracker/types';

const PROVIDER_COLORS: Record<string, string> = {
  gemini: '#4285f4',
  claude: '#d97706',
  groq: '#22c55e',
};

function formatCost(cents: number): string {
  if (cents === 0) { return 'Free'; }
  if (cents < 1) { return `$${(cents / 100).toFixed(4)}`; }
  return `$${(cents / 100).toFixed(2)}`;
}

function StatCard({ title, value, subtitle }: { title: string; value: string; subtitle?: string }) {
  return (
    <Card>
      <CardContent sx={{ textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">{title}</Typography>
        <Typography variant="h4" sx={{ fontWeight: 700, my: 1 }}>{value}</Typography>
        {subtitle && <Typography variant="caption" color="text.secondary">{subtitle}</Typography>}
      </CardContent>
    </Card>
  );
}

function AlertSeverityMap(level: CostAlert['level']): 'info' | 'warning' | 'error' {
  if (level === 'critical') return 'error';
  if (level === 'warning') return 'warning';
  return 'info';
}

export default function CostsPage() {
  const [days, setDays] = useState(30);
  const { data, isLoading, error } = useCostDashboard(days);
  const { data: alerts } = useCostAlerts();

  const handleExportCsv = () => {
    const url = getExportUrl(days);
    window.open(url, '_blank');
  };

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Skeleton variant="text" width={200} height={40} sx={{ mb: 2 }} />
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map((i) => (
            <Grid item xs={6} md={3} key={i}><Skeleton variant="rectangular" height={120} /></Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  if (error || !data) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Failed to load cost data.</Alert>
      </Box>
    );
  }

  const { summary, by_provider, by_module, recommendations, recent_calls } = data;
  const maxProviderCost = Math.max(...by_provider.map((p) => p.total_cost_cents), 1);

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">AI Cost Tracker</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button variant="outlined" size="small" onClick={handleExportCsv}>
            Export CSV
          </Button>
          <Select value={days} onChange={(e) => setDays(Number(e.target.value))} size="small">
            <MenuItem value={7}>Last 7 days</MenuItem>
            <MenuItem value={30}>Last 30 days</MenuItem>
            <MenuItem value={90}>Last 90 days</MenuItem>
            <MenuItem value={365}>Last year</MenuItem>
          </Select>
        </Box>
      </Box>

      {/* Budget Alerts */}
      {alerts && alerts.length > 0 && alerts.some((a) => a.level !== 'info' || a.metric !== 'all_clear') && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Budget Alerts</Typography>
            {alerts.map((alert, i) => (
              <Alert
                key={i}
                severity={AlertSeverityMap(alert.level)}
                sx={{ mb: 1 }}
              >
                <Typography variant="subtitle2">{alert.title}</Typography>
                {alert.message}
              </Alert>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={6} md={3}>
          <StatCard title="Total Cost" value={formatCost(summary.total_cost_cents)} subtitle={`${summary.period_start} - ${summary.period_end}`} />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard title="Total Calls" value={summary.total_calls.toLocaleString()} />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard title="Total Tokens" value={summary.total_tokens.toLocaleString()} />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard title="Avg Latency" value={`${summary.avg_latency_ms.toFixed(0)}ms`} />
        </Grid>
      </Grid>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Provider Breakdown */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Cost by Provider</Typography>
              {by_provider.length === 0 ? (
                <Typography variant="body2" color="text.secondary">No usage data yet.</Typography>
              ) : (
                by_provider.map((p) => (
                  <Box key={p.provider} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: PROVIDER_COLORS[p.provider] || '#999' }} />
                        <Typography variant="body2" fontWeight={600}>{p.provider}</Typography>
                        <Chip label={p.label} size="small" variant="outlined" />
                      </Box>
                      <Typography variant="body2">{formatCost(p.total_cost_cents)} | {p.total_calls} calls</Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(p.total_cost_cents / maxProviderCost) * 100}
                      sx={{ height: 8, borderRadius: 4, bgcolor: 'grey.100', '& .MuiLinearProgress-bar': { bgcolor: PROVIDER_COLORS[p.provider] || '#999' } }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {p.avg_latency_ms.toFixed(0)}ms avg | {p.success_rate.toFixed(0)}% success | {p.total_tokens.toLocaleString()} tokens
                    </Typography>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Module Breakdown */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Cost by Module</Typography>
              {by_module.length === 0 ? (
                <Typography variant="body2" color="text.secondary">No usage data yet.</Typography>
              ) : (
                by_module.map((m) => (
                  <Box key={m.module} sx={{ display: 'flex', justifyContent: 'space-between', py: 1, borderBottom: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="body2" fontWeight={500}>{m.module}</Typography>
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="body2">{formatCost(m.total_cost_cents)}</Typography>
                      <Typography variant="caption" color="text.secondary">{m.total_calls} calls | {m.total_tokens.toLocaleString()} tokens</Typography>
                    </Box>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Optimization Recommendations</Typography>
            {recommendations.map((rec, i) => (
              <Alert
                key={i}
                severity={rec.type === 'info' ? 'info' : 'warning'}
                sx={{ mb: 1 }}
              >
                {rec.message}
                {rec.potential_savings_cents > 0 && (
                  <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                    Potential savings: {formatCost(rec.potential_savings_cents)}
                  </Typography>
                )}
              </Alert>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Recent Calls */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Recent AI Calls</Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Provider</TableCell>
                  <TableCell>Module</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell align="right">Tokens</TableCell>
                  <TableCell align="right">Cost</TableCell>
                  <TableCell align="right">Latency</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Time</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recent_calls.map((call, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <Chip label={call.provider} size="small" sx={{ bgcolor: PROVIDER_COLORS[call.provider] || '#999', color: 'white' }} />
                    </TableCell>
                    <TableCell>{call.module}</TableCell>
                    <TableCell>{call.action}</TableCell>
                    <TableCell align="right">{call.total_tokens.toLocaleString()}</TableCell>
                    <TableCell align="right">{formatCost(call.cost_cents)}</TableCell>
                    <TableCell align="right">{call.latency_ms}ms</TableCell>
                    <TableCell>
                      <Chip label={call.success ? 'OK' : 'Error'} size="small" color={call.success ? 'success' : 'error'} variant="outlined" />
                    </TableCell>
                    <TableCell>{new Date(call.created_at).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
                {recent_calls.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>No AI calls recorded yet.</Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}
