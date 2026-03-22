'use client';

import { Box, Card, CardContent, LinearProgress, Skeleton, Typography } from '@mui/material';
import { useRouter } from 'next/navigation';

import { useQuota } from '@/features/billing/hooks/useBilling';

export default function QuotaWidget() {
  const { data: quota, isLoading } = useQuota();
  const router = useRouter();

  if (isLoading) {
    return <Skeleton variant="rectangular" height={100} />;
  }

  if (!quota) return null;

  const percent = Math.min(quota.usage_percent, 100);

  return (
    <Card
      sx={{ cursor: 'pointer' }}
      onClick={() => router.push('/billing')}
    >
      <CardContent sx={{ pb: '16px !important' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="subtitle2">Usage ({quota.plan.display_name})</Typography>
          <Typography variant="body2" color="text.secondary">
            {percent.toFixed(0)}%
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={percent}
          color={percent >= 100 ? 'error' : percent >= 80 ? 'warning' : 'primary'}
          sx={{ height: 6, borderRadius: 3 }}
        />
      </CardContent>
    </Card>
  );
}
