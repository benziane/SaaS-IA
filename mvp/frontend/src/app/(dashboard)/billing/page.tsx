'use client';

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  Skeleton,
  Typography,
} from '@mui/material';
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
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2" fontWeight={500}>
          {label}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {used.toLocaleString()} / {limit >= 999999 ? 'Unlimited' : limit.toLocaleString()}
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={percent}
        color={isExceeded ? 'error' : isWarning ? 'warning' : 'primary'}
        sx={{ height: 8, borderRadius: 4 }}
      />
    </Box>
  );
}

function PlanCard({ plan, isCurrent, onUpgrade }: { plan: Plan; isCurrent: boolean; onUpgrade?: () => void }) {
  return (
    <Card
      variant={isCurrent ? 'elevation' : 'outlined'}
      sx={{
        height: '100%',
        border: isCurrent ? '2px solid' : undefined,
        borderColor: isCurrent ? 'primary.main' : undefined,
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">{plan.display_name}</Typography>
          {isCurrent && <Chip label="Current" color="primary" size="small" />}
        </Box>
        <Typography variant="h4" sx={{ mb: 2 }}>
          {formatPrice(plan.price_cents)}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
          {plan.max_transcriptions_month >= 999999 ? 'Unlimited' : plan.max_transcriptions_month} transcriptions/month
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
          {plan.max_audio_minutes_month >= 999999 ? 'Unlimited' : plan.max_audio_minutes_month} audio minutes/month
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {plan.max_ai_calls_month >= 999999 ? 'Unlimited' : plan.max_ai_calls_month} AI calls/month
        </Typography>
        {!isCurrent && plan.price_cents > 0 && onUpgrade && (
          <Button variant="contained" fullWidth onClick={onUpgrade}>
            Upgrade to {plan.display_name}
          </Button>
        )}
        {isCurrent && plan.price_cents > 0 && (
          <Typography variant="caption" color="success.main">Active subscription</Typography>
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
      <Box sx={{ p: 3 }}>
        <Skeleton variant="text" width={200} height={40} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" height={200} sx={{ mb: 3 }} />
        <Grid container spacing={3}>
          {[1, 2, 3].map((i) => (
            <Grid item xs={12} md={4} key={i}>
              <Skeleton variant="rectangular" height={200} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  if (quotaError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Failed to load billing information. Please try again later.</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Billing & Usage
      </Typography>

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Payment successful! Your plan has been upgraded.
        </Alert>
      )}
      {canceled && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Checkout was canceled. No changes were made.
        </Alert>
      )}

      {/* Current Usage */}
      {quota && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">Current Usage</Typography>
              <Chip
                label={quota.plan.display_name}
                color="primary"
                variant="outlined"
              />
            </Box>

            {quota.usage_percent >= 80 && (
              <Alert
                severity={quota.usage_percent >= 100 ? 'error' : 'warning'}
                sx={{ mb: 2 }}
              >
                {quota.usage_percent >= 100
                  ? 'You have exceeded your quota. Please upgrade your plan to continue.'
                  : 'You are approaching your usage limit. Consider upgrading your plan.'}
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

            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Billing period: {quota.period_start} to {quota.period_end}
            </Typography>
            {quota.plan.price_cents > 0 && (
              <Button
                variant="outlined"
                size="small"
                sx={{ mt: 2 }}
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
      <Typography variant="h6" sx={{ mb: 2 }}>
        Available Plans
      </Typography>
      <Grid container spacing={3}>
        {plans?.map((plan) => (
          <Grid item xs={12} md={4} key={plan.id}>
            <PlanCard
              plan={plan}
              isCurrent={quota?.plan.id === plan.id}
              onUpgrade={() => checkoutMutation.mutate(plan.name)}
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
