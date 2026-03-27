'use client';

import { useState } from 'react';
import { Shield, ShieldCheck, EyeOff, Bug, History, Loader2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/lib/design-hub/components/Button';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Switch } from '@/lib/design-hub/components/Switch';
import { Separator } from '@/lib/design-hub/components/Separator';

import {
  useAuditLogs, useGuardrails, useScanContent, useSecurityDashboard,
} from '@/features/security/hooks/useSecurity';

const SEVERITY_COLORS: Record<string, 'secondary' | 'default' | 'warning' | 'destructive'> = {
  low: 'default',
  medium: 'warning',
  high: 'destructive',
  critical: 'destructive',
};

export default function SecurityPage() {
  const { data: dashboard, isLoading: dashLoading } = useSecurityDashboard();
  const { data: auditLogs } = useAuditLogs();
  const { data: _guardrails } = useGuardrails();
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
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
          <Shield className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Security Guardian</h1>
          <p className="text-xs text-[var(--text-mid)]">PII detection and security analysis</p>
        </div>
      </div>

      {/* Dashboard Stats */}
      {dashLoading ? <Skeleton className="h-[100px]" /> : dashboard && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          {[
            { label: 'Total Scans', value: dashboard.total_scans, colorClass: 'text-[var(--accent)]' },
            { label: 'Issues Found', value: dashboard.issues_found, colorClass: 'text-red-400' },
            { label: 'PII Detected', value: dashboard.pii_detected, colorClass: 'text-amber-400' },
            { label: 'Prompts Blocked', value: dashboard.prompts_blocked, colorClass: 'text-red-400' },
            { label: 'Audit Entries', value: dashboard.audit_entries, colorClass: 'text-blue-400' },
          ].map((stat) => (
            <div key={stat.label} className="surface-card p-5 text-center">
              <p className={`text-2xl font-bold ${stat.colorClass}`}>{stat.value}</p>
              <p className="text-xs text-[var(--text-low)]">{stat.label}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Scanner */}
        <div className="md:col-span-7">
          <div className="surface-card p-5">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4 flex items-center gap-2">
              <Bug className="h-5 w-5" /> Content Scanner
            </h2>
            <Textarea
              rows={6}
              placeholder="Paste text to scan for PII, prompt injection, and safety issues..."
              value={scanText}
              onChange={(e) => setScanText(e.target.value)}
              className="mb-4"
            />

            <div className="flex flex-wrap gap-1.5 mb-4">
              {['pii', 'prompt_injection', 'content_safety'].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => toggleScanType(type)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                    scanTypes.includes(type)
                      ? 'bg-[var(--accent)] text-[var(--bg-app)]'
                      : 'border border-[var(--border)] text-[var(--text-mid)] hover:bg-[var(--bg-elevated)]'
                  }`}
                >
                  {type.replace('_', ' ')}
                </button>
              ))}
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-[var(--text-mid)]">
                <Switch checked={autoRedact} onCheckedChange={setAutoRedact} />
                <EyeOff className="h-4 w-4" />
                Auto-redact PII
              </label>
              <Button onClick={handleScan} disabled={!scanText.trim() || scanMutation.isPending}>
                {scanMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <ShieldCheck className="h-4 w-4 mr-1" />}
                Scan
              </Button>
            </div>

            {/* Scan Results */}
            {scanMutation.data && (
              <div className="mt-6">
                <Separator className="mb-4" />
                <div className="flex items-center gap-2 mb-4">
                  <h3 className="text-base font-semibold text-[var(--text-high)]">Scan Results</h3>
                  <Badge variant={scanMutation.data.status === 'clean' ? 'success' : 'destructive'}>
                    {scanMutation.data.status}
                  </Badge>
                  {scanMutation.data.severity && (
                    <Badge variant={SEVERITY_COLORS[scanMutation.data.severity] || 'secondary'}>
                      {scanMutation.data.severity}
                    </Badge>
                  )}
                </div>

                {scanMutation.data.findings.length === 0 ? (
                  <Alert variant="success">
                    <AlertDescription>No security issues detected. Content is clean.</AlertDescription>
                  </Alert>
                ) : (
                  scanMutation.data.findings.map((f, i) => (
                    <Alert
                      key={i}
                      variant={f.severity === 'critical' || f.severity === 'high' ? 'destructive' : 'warning'}
                      className="mb-2"
                    >
                      <AlertDescription>
                        <span className="font-semibold">[{f.type}] {f.description}</span>
                        {f.suggestion && <span className="block text-xs mt-0.5">{f.suggestion}</span>}
                      </AlertDescription>
                    </Alert>
                  ))
                )}

                {scanMutation.data.auto_redacted && scanMutation.data.redacted_text && (
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold text-[var(--text-high)] mb-2">Redacted Text</h4>
                    <div className="p-3 bg-[var(--bg-elevated)] rounded font-mono text-sm whitespace-pre-wrap">
                      {scanMutation.data.redacted_text}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Audit Log + Guardrails */}
        <div className="md:col-span-5 space-y-6">
          <div className="surface-card p-5">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4 flex items-center gap-2">
              <History className="h-5 w-5" /> Recent Audit Log
            </h2>
            {!auditLogs?.length ? (
              <p className="text-[var(--text-mid)]">No audit entries yet</p>
            ) : (
              auditLogs.slice(0, 10).map((log) => (
                <div key={log.id} className="mb-2 pb-2 border-b border-[var(--border)] last:border-0">
                  <div className="flex justify-between">
                    <div className="flex gap-1">
                      <Badge variant="outline" className="text-xs">{log.action}</Badge>
                      <Badge variant="outline" className="text-xs">{log.module}</Badge>
                    </div>
                    {log.flagged && <Badge variant="destructive" className="text-xs">FLAGGED</Badge>}
                  </div>
                  <p className="text-xs text-[var(--text-low)] mt-0.5">
                    {log.provider && `${log.provider} | `}{log.tokens_used} tokens | {new Date(log.created_at).toLocaleString()}
                  </p>
                </div>
              ))
            )}
          </div>

          {/* Risk Distribution */}
          {dashboard && (
            <div className="surface-card p-5">
              <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">Risk Distribution</h2>
              {Object.entries(dashboard.risk_distribution).map(([level, count]) => (
                <div key={level} className="mb-2">
                  <div className="flex justify-between mb-1">
                    <Badge variant={SEVERITY_COLORS[level] || 'secondary'} className="text-xs">{level}</Badge>
                    <span className="text-sm text-[var(--text-high)]">{count}</span>
                  </div>
                  <Progress
                    value={dashboard.issues_found > 0 ? (count / Math.max(dashboard.issues_found, 1)) * 100 : 0}
                    className={`h-1.5 ${
                      level === 'critical' || level === 'high' ? '[&>div]:bg-red-500' :
                      level === 'medium' ? '[&>div]:bg-amber-500' :
                      '[&>div]:bg-blue-500'
                    }`}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
