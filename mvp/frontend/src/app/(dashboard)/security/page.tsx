'use client';

import { useState } from 'react';
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  Dialog, DialogActions, DialogContent, DialogTitle, Divider,
  FormControlLabel, Grid, LinearProgress, Skeleton, Switch,
  TextField, Typography,
} from '@mui/material';
import SecurityIcon from '@mui/icons-material/Security';
import ShieldIcon from '@mui/icons-material/Shield';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import BugReportIcon from '@mui/icons-material/BugReport';
import HistoryIcon from '@mui/icons-material/History';

import {
  useAuditLogs, useGuardrails, useScanContent, useSecurityDashboard,
} from '@/features/security/hooks/useSecurity';

const SEVERITY_COLORS: Record<string, 'default' | 'info' | 'warning' | 'error'> = {
  low: 'info', medium: 'warning', high: 'error', critical: 'error',
};

export default function SecurityPage() {
  const { data: dashboard, isLoading: dashLoading } = useSecurityDashboard();
  const { data: auditLogs } = useAuditLogs();
  const { data: guardrails } = useGuardrails();
  const scanMutation = useScanContent();

  const [scanText, setScanText] = useState('');
  const [autoRedact, setAutoRedact] = useState(false);
  const [scanTypes, setScanTypes] = useState(['pii', 'prompt_injection', 'content_safety']);

  const handleScan = () => {
    if (!scanText.trim()) return;
    scanMutation.mutate({ text: scanText, scan_types: scanTypes, auto_redact: autoRedact });
  };

  const toggleScanType = (type: string) => {
    setScanTypes((prev) => prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SecurityIcon color="primary" /> Security Guardian
        </Typography>
        <Typography variant="body2" color="text.secondary">
          AI safety guardrails, PII detection, audit trails, and compliance monitoring
        </Typography>
      </Box>

      {/* Dashboard Stats */}
      {dashLoading ? <Skeleton variant="rectangular" height={100} sx={{ mb: 3 }} /> : dashboard && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[
            { label: 'Total Scans', value: dashboard.total_scans, color: 'primary.main' },
            { label: 'Issues Found', value: dashboard.issues_found, color: 'error.main' },
            { label: 'PII Detected', value: dashboard.pii_detected, color: 'warning.main' },
            { label: 'Prompts Blocked', value: dashboard.prompts_blocked, color: 'error.main' },
            { label: 'Audit Entries', value: dashboard.audit_entries, color: 'info.main' },
          ].map((stat) => (
            <Grid item xs={6} sm={2.4} key={stat.label}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center', py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Typography variant="h4" sx={{ color: stat.color }}>{stat.value}</Typography>
                  <Typography variant="caption" color="text.secondary">{stat.label}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Grid container spacing={3}>
        {/* Scanner */}
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <BugReportIcon /> Content Scanner
              </Typography>
              <TextField fullWidth multiline rows={6} label="Text to scan"
                placeholder="Paste text to scan for PII, prompt injection, and safety issues..."
                value={scanText} onChange={(e) => setScanText(e.target.value)} sx={{ mb: 2 }} />

              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                {['pii', 'prompt_injection', 'content_safety'].map((type) => (
                  <Chip key={type} label={type.replace('_', ' ')} variant={scanTypes.includes(type) ? 'filled' : 'outlined'}
                    color={scanTypes.includes(type) ? 'primary' : 'default'}
                    onClick={() => toggleScanType(type)} />
                ))}
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <FormControlLabel control={<Switch checked={autoRedact} onChange={(e) => setAutoRedact(e.target.checked)} />}
                  label={<Typography variant="body2"><VisibilityOffIcon sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'text-bottom' }} />Auto-redact PII</Typography>} />
                <Button variant="contained" startIcon={
                  scanMutation.isPending ? <CircularProgress size={16} color="inherit" /> : <ShieldIcon />
                } onClick={handleScan} disabled={!scanText.trim() || scanMutation.isPending}>
                  Scan
                </Button>
              </Box>

              {/* Scan Results */}
              {scanMutation.data && (
                <Box sx={{ mt: 3 }}>
                  <Divider sx={{ mb: 2 }} />
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <Typography variant="subtitle1">Scan Results</Typography>
                    <Chip label={scanMutation.data.status} size="small"
                      color={scanMutation.data.status === 'clean' ? 'success' : 'error'} />
                    {scanMutation.data.severity && (
                      <Chip label={scanMutation.data.severity} size="small"
                        color={SEVERITY_COLORS[scanMutation.data.severity] || 'default'} />
                    )}
                  </Box>

                  {scanMutation.data.findings.length === 0 ? (
                    <Alert severity="success">No security issues detected. Content is clean.</Alert>
                  ) : (
                    scanMutation.data.findings.map((f, i) => (
                      <Alert key={i} severity={f.severity === 'critical' || f.severity === 'high' ? 'error' : 'warning'}
                        sx={{ mb: 1 }}>
                        <Typography variant="subtitle2">[{f.type}] {f.description}</Typography>
                        {f.suggestion && <Typography variant="caption">{f.suggestion}</Typography>}
                      </Alert>
                    ))
                  )}

                  {scanMutation.data.auto_redacted && scanMutation.data.redacted_text && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>Redacted Text</Typography>
                      <Box sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 1, fontFamily: 'monospace', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>
                        {scanMutation.data.redacted_text}
                      </Box>
                    </Box>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Audit Log + Guardrails */}
        <Grid item xs={12} md={5}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <HistoryIcon /> Recent Audit Log
              </Typography>
              {!auditLogs?.length ? (
                <Typography color="text.secondary">No audit entries yet</Typography>
              ) : (
                auditLogs.slice(0, 10).map((log) => (
                  <Box key={log.id} sx={{ mb: 1, pb: 1, borderBottom: 1, borderColor: 'divider' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <Chip label={log.action} size="small" variant="outlined" />
                        <Chip label={log.module} size="small" variant="outlined" />
                      </Box>
                      {log.flagged && <Chip label="FLAGGED" size="small" color="error" />}
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {log.provider && `${log.provider} | `}{log.tokens_used} tokens | {new Date(log.created_at).toLocaleString()}
                    </Typography>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>

          {/* Risk Distribution */}
          {dashboard && (
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>Risk Distribution</Typography>
                {Object.entries(dashboard.risk_distribution).map(([level, count]) => (
                  <Box key={level} sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Chip label={level} size="small" color={SEVERITY_COLORS[level] || 'default'} />
                      <Typography variant="body2">{count}</Typography>
                    </Box>
                    <LinearProgress variant="determinate"
                      value={dashboard.issues_found > 0 ? (count / Math.max(dashboard.issues_found, 1)) * 100 : 0}
                      color={level === 'critical' || level === 'high' ? 'error' : level === 'medium' ? 'warning' : 'info'} />
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
