'use client';

import { Card, CardContent } from '@/lib/design-hub/components/Card';
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
    <Card
      className={`h-full ${isCurrent ? 'border-2 border-[var(--accent)]' : ''}`}
    >
      <CardContent className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-[var(--text-high)]">{plan.display_name}</h3>
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
      </CardContent>
    </Card>
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
      <div className="p-6">
        <Skeleton className="h-10 w-48 mb-4" />
        <Skeleton className="h-[200px] w-full mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-[200px] w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (quotaError) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertDescription>Failed to load billing information. Please try again later.</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-[var(--text-high)] mb-6">
        Billing & Usage
      </h1>

      {success && (
        <Alert variant="success" className="mb-6">
          <AlertDescription>Payment successful! Your plan has been upgraded.</AlertDescription>
        </Alert>
      )}
      {canceled && (
        <Alert variant="info" className="mb-6">
          <AlertDescription>Checkout was canceled. No changes were made.</AlertDescription>
        </Alert>
      )}

      {/* Current Usage */}
      {quota && (
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold text-[var(--text-high)]">Current Usage</h2>
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
          </CardContent>
        </Card>
      )}

      {/* Plans Comparison */}
      <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">
        Available Plans
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
  );
}
