'use client';

import { useState } from 'react';
import { Download } from 'lucide-react';

import { Card, CardContent } from '@/lib/design-hub/components/Card';
import { Button } from '@/lib/design-hub/components/Button';
import { Badge } from '@/lib/design-hub/components/Badge';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/lib/design-hub/components/Alert';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/lib/design-hub/components/Select';
import { Progress } from '@/components/ui/progress';

import { useCostDashboard, useCostAlerts } from '@/features/cost-tracker/hooks/useCosts';
import { getExportUrl } from '@/features/cost-tracker/api';
import type { CostAlert } from '@/features/cost-tracker/types';

function formatCost(cents: number): string {
  if (cents === 0) { return 'Free'; }
  if (cents < 1) { return `$${(cents / 100).toFixed(4)}`; }
  return `$${(cents / 100).toFixed(2)}`;
}

function StatCard({ title, value, subtitle }: { title: string; value: string; subtitle?: string }) {
  return (
    <Card>
      <CardContent className="p-6 text-center">
        <p className="text-sm text-[var(--text-mid)]">{title}</p>
        <p className="text-3xl font-bold text-[var(--text-high)] my-2">{value}</p>
        {subtitle && <p className="text-xs text-[var(--text-mid)]">{subtitle}</p>}
      </CardContent>
    </Card>
  );
}

function AlertSeverityMap(level: CostAlert['level']): 'destructive' | 'warning' | 'info' {
  if (level === 'critical') return 'destructive';
  if (level === 'warning') return 'warning';
  return 'info';
}

export default function CostsPage() {
  const [days, setDays] = useState('30');
  const { data, isLoading, error } = useCostDashboard(Number(days));
  const { data: alerts } = useCostAlerts();

  const handleExportCsv = () => {
    const url = getExportUrl(Number(days));
    window.open(url, '_blank');
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <Skeleton className="h-10 w-48 mb-4" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-[120px] w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertDescription>Failed to load cost data.</AlertDescription>
        </Alert>
      </div>
    );
  }

  const { summary, by_provider, by_module, recommendations, recent_calls } = data;
  const maxProviderCost = Math.max(...by_provider.map((p) => p.total_cost_cents), 1);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-[var(--text-high)]">AI Cost Tracker</h1>
        <div className="flex gap-3 items-center">
          <Button variant="outline" size="sm" onClick={handleExportCsv}>
            <Download className="h-4 w-4 mr-1" />
            Export CSV
          </Button>
          <Select value={days} onValueChange={setDays}>
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="90">Last 90 days</SelectItem>
              <SelectItem value="365">Last year</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Budget Alerts */}
      {alerts && alerts.length > 0 && alerts.some((a) => a.level !== 'info' || a.metric !== 'all_clear') && (
        <Card className="mb-6">
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">Budget Alerts</h2>
            <div className="space-y-2">
              {alerts.map((alert, i) => (
                <Alert key={i} variant={AlertSeverityMap(alert.level)}>
                  <AlertTitle>{alert.title}</AlertTitle>
                  <AlertDescription>{alert.message}</AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
        <StatCard title="Total Cost" value={formatCost(summary.total_cost_cents)} subtitle={`${summary.period_start} - ${summary.period_end}`} />
        <StatCard title="Total Calls" value={summary.total_calls.toLocaleString()} />
        <StatCard title="Total Tokens" value={summary.total_tokens.toLocaleString()} />
        <StatCard title="Avg Latency" value={`${summary.avg_latency_ms.toFixed(0)}ms`} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Provider Breakdown */}
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">Cost by Provider</h2>
            {by_provider.length === 0 ? (
              <p className="text-sm text-[var(--text-mid)]">No usage data yet.</p>
            ) : (
              <div className="space-y-4">
                {by_provider.map((p) => (
                  <div key={p.provider}>
                    <div className="flex justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-3 h-3 rounded-full inline-block ${
                            p.provider === 'gemini' ? 'bg-[#4285f4]' :
                            p.provider === 'claude' ? 'bg-[#d97706]' :
                            p.provider === 'groq' ? 'bg-[#22c55e]' :
                            'bg-[#999]'
                          }`}
                        />
                        <span className="text-sm font-semibold text-[var(--text-high)]">{p.provider}</span>
                        <Badge variant="outline">{p.label}</Badge>
                      </div>
                      <span className="text-sm text-[var(--text-mid)]">{formatCost(p.total_cost_cents)} | {p.total_calls} calls</span>
                    </div>
                    <Progress
                      value={(p.total_cost_cents / maxProviderCost) * 100}
                      className="h-2"
                    />
                    <p className="text-xs text-[var(--text-mid)] mt-1">
                      {p.avg_latency_ms.toFixed(0)}ms avg | {p.success_rate.toFixed(0)}% success | {p.total_tokens.toLocaleString()} tokens
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Module Breakdown */}
        <Card>
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">Cost by Module</h2>
            {by_module.length === 0 ? (
              <p className="text-sm text-[var(--text-mid)]">No usage data yet.</p>
            ) : (
              <div className="divide-y divide-[var(--border)]">
                {by_module.map((m) => (
                  <div key={m.module} className="flex justify-between py-2">
                    <span className="text-sm font-medium text-[var(--text-high)]">{m.module}</span>
                    <div className="text-right">
                      <p className="text-sm text-[var(--text-high)]">{formatCost(m.total_cost_cents)}</p>
                      <p className="text-xs text-[var(--text-mid)]">{m.total_calls} calls | {m.total_tokens.toLocaleString()} tokens</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card className="mb-8">
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">Optimization Recommendations</h2>
            <div className="space-y-2">
              {recommendations.map((rec, i) => (
                <Alert key={i} variant={rec.type === 'info' ? 'info' : 'warning'}>
                  <AlertDescription>
                    {rec.message}
                    {rec.potential_savings_cents > 0 && (
                      <span className="block text-xs mt-1">
                        Potential savings: {formatCost(rec.potential_savings_cents)}
                      </span>
                    )}
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Calls */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">Recent AI Calls</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  <th className="text-left py-2 px-3 text-xs font-semibold text-[var(--text-mid)]">Provider</th>
                  <th className="text-left py-2 px-3 text-xs font-semibold text-[var(--text-mid)]">Module</th>
                  <th className="text-left py-2 px-3 text-xs font-semibold text-[var(--text-mid)]">Action</th>
                  <th className="text-right py-2 px-3 text-xs font-semibold text-[var(--text-mid)]">Tokens</th>
                  <th className="text-right py-2 px-3 text-xs font-semibold text-[var(--text-mid)]">Cost</th>
                  <th className="text-right py-2 px-3 text-xs font-semibold text-[var(--text-mid)]">Latency</th>
                  <th className="text-left py-2 px-3 text-xs font-semibold text-[var(--text-mid)]">Status</th>
                  <th className="text-left py-2 px-3 text-xs font-semibold text-[var(--text-mid)]">Time</th>
                </tr>
              </thead>
              <tbody>
                {recent_calls.map((call, i) => (
                  <tr key={i} className="border-b border-[var(--border)] last:border-0">
                    <td className="py-2 px-3">
                      <Badge
                        className={`text-white ${
                          call.provider === 'gemini' ? 'bg-[#4285f4]' :
                          call.provider === 'claude' ? 'bg-[#d97706]' :
                          call.provider === 'groq' ? 'bg-[#22c55e]' :
                          'bg-[#999]'
                        }`}
                      >
                        {call.provider}
                      </Badge>
                    </td>
                    <td className="py-2 px-3 text-[var(--text-high)]">{call.module}</td>
                    <td className="py-2 px-3 text-[var(--text-high)]">{call.action}</td>
                    <td className="py-2 px-3 text-right text-[var(--text-high)]">{call.total_tokens.toLocaleString()}</td>
                    <td className="py-2 px-3 text-right text-[var(--text-high)]">{formatCost(call.cost_cents)}</td>
                    <td className="py-2 px-3 text-right text-[var(--text-high)]">{call.latency_ms}ms</td>
                    <td className="py-2 px-3">
                      <Badge variant={call.success ? 'success' : 'destructive'}>
                        {call.success ? 'OK' : 'Error'}
                      </Badge>
                    </td>
                    <td className="py-2 px-3 text-[var(--text-mid)]">{new Date(call.created_at).toLocaleString()}</td>
                  </tr>
                ))}
                {recent_calls.length === 0 && (
                  <tr>
                    <td colSpan={8} className="text-center py-4">
                      <p className="text-sm text-[var(--text-mid)]">No AI calls recorded yet.</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
