'use client';

import { CreditCard } from 'lucide-react';
import { Button } from '@/lib/design-hub/components/Button';
import { Badge } from '@/lib/design-hub/components/Badge';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Progress } from '@/components/ui/progress';
import { useSearchParams } from 'next/navigation';

import { useCheckout, usePlans, usePortal, useQuota } from '@/features/billing/hooks/useBilling';
import type { Plan } from '@/features/billing/types';

function formatPrice(cents: number): string {
  if (cents === 0) { return 'Free'; }
  return `${(cents / 100).toFixed(0)} EUR/month`;
}

function QuotaBar({
  label,
  used,
  limit,
}: {
  label: string;
  used: number;
  limit: number;
}) {
  const percent = limit > 0 ? Math.min((used / limit) * 100, 100) : 0;
  const isWarning = percent >= 80;
  const isExceeded = percent >= 100;

  return (
    <div className="mb-4">
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium text-[var(--text-high)]">
          {label}
        </span>
        <span className="text-sm text-[var(--text-mid)]">
          {used.toLocaleString()} / {limit >= 999999 ? 'Unlimited' : limit.toLocaleString()}
        </span>
      </div>
      <Progress
        value={percent}
        className={`h-2 ${isExceeded ? '[&>div]:bg-red-500' : isWarning ? '[&>div]:bg-amber-500' : ''}`}
      />
    </div>
  );
}

function PlanCard({ plan, isCurrent, onUpgrade }: { plan: Plan; isCurrent: boolean; onUpgrade?: () => void }) {
  return (
    <div className={`surface-card p-5 h-full ${isCurrent ? 'border-l-4 border-l-[var(--accent)]' : ''}`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-base font-semibold text-[var(--text-high)]">{plan.display_name}</h3>
        {isCurrent && <Badge>Current</Badge>}
      </div>
      <p className="text-3xl font-bold text-[var(--text-high)] mb-4">
        {formatPrice(plan.price_cents)}
      </p>
      <p className="text-sm text-[var(--text-mid)] mb-1">
        {plan.max_transcriptions_month >= 999999 ? 'Unlimited' : plan.max_transcriptions_month} transcriptions/month
      </p>
      <p className="text-sm text-[var(--text-mid)] mb-1">
        {plan.max_audio_minutes_month >= 999999 ? 'Unlimited' : plan.max_audio_minutes_month} audio minutes/month
      </p>
      <p className="text-sm text-[var(--text-mid)] mb-4">
        {plan.max_ai_calls_month >= 999999 ? 'Unlimited' : plan.max_ai_calls_month} AI calls/month
      </p>
      {!isCurrent && plan.price_cents > 0 && onUpgrade && (
        <Button className="w-full" onClick={onUpgrade}>
          Upgrade to {plan.display_name}
        </Button>
      )}
      {isCurrent && plan.price_cents > 0 && (
        <p className="text-xs text-green-400">Active subscription</p>
      )}
    </div>
  );
}

export default function BillingPage() {
  const searchParams = useSearchParams();
  const success = searchParams.get('success');
  const canceled = searchParams.get('canceled');

  const { data: quota, isLoading: quotaLoading, error: quotaError } = useQuota();
  const { data: plans, isLoading: plansLoading } = usePlans();
  const checkoutMutation = useCheckout();
  const portalMutation = usePortal();

  if (quotaLoading || plansLoading) {
    return (
      <div className="p-5 space-y-5 animate-enter">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-[200px] w-full" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-[200px] w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (quotaError) {
    return (
      <div className="p-5 space-y-5 animate-enter">
        <Alert variant="destructive">
          <AlertDescription>Failed to load billing information. Please try again later.</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
          <CreditCard className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">Billing & Usage</h1>
          <p className="text-xs text-[var(--text-mid)]">Manage your subscription and monitor usage quotas</p>
        </div>
      </div>

      {success && (
        <Alert variant="success">
          <AlertDescription>Payment successful! Your plan has been upgraded.</AlertDescription>
        </Alert>
      )}
      {canceled && (
        <Alert variant="info">
          <AlertDescription>Checkout was canceled. No changes were made.</AlertDescription>
        </Alert>
      )}

      {/* Current Usage */}
      {quota && (
        <div className="surface-card p-5">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-base font-semibold text-[var(--text-high)]">Current Usage</h2>
            <Badge variant="outline">{quota.plan.display_name}</Badge>
          </div>

          {quota.usage_percent >= 80 && (
            <Alert
              variant={quota.usage_percent >= 100 ? 'destructive' : 'warning'}
              className="mb-4"
            >
              <AlertDescription>
                {quota.usage_percent >= 100
                  ? 'You have exceeded your quota. Please upgrade your plan to continue.'
                  : 'You are approaching your usage limit. Consider upgrading your plan.'}
              </AlertDescription>
            </Alert>
          )}

          <QuotaBar
            label="Transcriptions"
            used={quota.transcriptions_used}
            limit={quota.transcriptions_limit}
          />
          <QuotaBar
            label="Audio Minutes"
            used={quota.audio_minutes_used}
            limit={quota.audio_minutes_limit}
          />
          <QuotaBar
            label="AI Calls"
            used={quota.ai_calls_used}
            limit={quota.ai_calls_limit}
          />

          <p className="text-sm text-[var(--text-mid)] mt-4">
            Billing period: {quota.period_start} to {quota.period_end}
          </p>
          {quota.plan.price_cents > 0 && (
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={() => portalMutation.mutate()}
              disabled={portalMutation.isPending}
            >
              Manage Subscription
            </Button>
          )}
        </div>
      )}

      {/* Plans Comparison */}
      <div>
        <h2 className="text-base font-semibold text-[var(--text-high)] mb-4">Available Plans</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {plans?.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              isCurrent={quota?.plan.id === plan.id}
              onUpgrade={() => checkoutMutation.mutate(plan.name)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
