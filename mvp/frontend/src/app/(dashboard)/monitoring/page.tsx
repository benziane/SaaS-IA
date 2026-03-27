'use client';

import { useEffect, useState } from 'react';
import { Activity, Gauge } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
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
  const [days, setDays] = useState('7');

  useEffect(() => {
    setLoading(true);
    apiClient.get(`/api/monitoring/dashboard?days=${days}`)
      .then(res => setData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) return <div className="p-5"><Skeleton className="h-96 rounded-lg" /></div>;
  if (!data) return <div className="p-5"><p className="text-[var(--text-mid)]">No monitoring data available</p></div>;

  const kpis = [
    { label: 'Total Calls', value: data.total_calls.toLocaleString(), color: 'text-[var(--accent)]' },
    { label: 'Success Rate', value: `${data.success_rate}%`, color: data.success_rate > 95 ? 'text-green-600' : 'text-yellow-600' },
    { label: 'Total Tokens', value: data.total_tokens.toLocaleString(), color: 'text-blue-500' },
    { label: 'Total Cost', value: `$${data.total_cost_usd.toFixed(4)}`, color: 'text-red-500' },
    { label: 'Avg Latency', value: `${data.avg_latency_ms}ms`, color: data.avg_latency_ms < 2000 ? 'text-green-600' : 'text-yellow-600' },
  ];

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
            <Activity className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">AI Monitoring</h1>
            <p className="text-xs text-[var(--text-mid)]">LLM observability - calls, latency, cost, providers, errors</p>
          </div>
        </div>
        <Select value={days} onValueChange={setDays}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="Period" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">24h</SelectItem>
            <SelectItem value="7">7 days</SelectItem>
            <SelectItem value="30">30 days</SelectItem>
            <SelectItem value="90">90 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="surface-card p-5 text-center">
            <p className={`text-3xl font-bold ${kpi.color}`}>{kpi.value}</p>
            <span className="text-xs text-[var(--text-mid)]">{kpi.label}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Provider Comparison */}
        <div className="surface-card p-5">
          <h3 className="text-lg font-semibold text-[var(--text-high)] flex items-center gap-2 mb-4">
            <Gauge className="h-5 w-5" /> Provider Performance
          </h3>
          {data.providers.map((p: Record<string, unknown>) => (
            <div key={p.provider as string} className="mb-4">
              <div className="flex justify-between mb-1">
                <div className="flex gap-1">
                  <Badge>{p.provider as string}</Badge>
                  <Badge variant="outline">{p.calls as number} calls</Badge>
                  <Badge variant="outline">{p.avg_latency_ms as number}ms</Badge>
                </div>
                <span className="text-xs text-[var(--text-mid)]">{p.success_rate as number}% success</span>
              </div>
              <Progress
                value={p.success_rate as number}
                className={`h-2 ${(p.success_rate as number) > 95 ? '' : '[&>div]:bg-yellow-500'}`}
              />
            </div>
          ))}
        </div>

        {/* Module Usage */}
        <div className="surface-card p-5">
          <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4">Module Usage</h3>
          {data.modules.map((m: Record<string, unknown>) => (
            <div key={m.module as string} className="flex justify-between mb-2 pb-2 border-b border-[var(--border)]">
              <Badge variant="outline">{m.module as string}</Badge>
              <div className="flex gap-2">
                <span className="text-sm text-[var(--text-high)]">{m.calls as number} calls</span>
                <span className="text-xs text-[var(--text-mid)]">${((m.cost_cents as number) / 100).toFixed(4)}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Errors */}
        {data.recent_errors.length > 0 && (
          <div className="md:col-span-2">
            <div className="surface-card p-5">
              <h3 className="text-lg font-semibold text-red-500 mb-4">Recent Errors</h3>
              {data.recent_errors.map((e: Record<string, unknown>, i: number) => (
                <div key={i} className="mb-2 pb-2 border-b border-[var(--border)]">
                  <div className="flex gap-1 mb-1">
                    <Badge variant="destructive">{e.provider as string}</Badge>
                    <Badge variant="outline">{e.module as string}</Badge>
                    <Badge variant="outline">{e.action as string}</Badge>
                  </div>
                  <span className="text-xs text-red-500">{e.error as string}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
