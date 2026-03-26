'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';

import { useQuota } from '@/features/billing/hooks/useBilling';

export default function QuotaWidget() {
  const { data: quota, isLoading } = useQuota();
  const router = useRouter();

  if (isLoading) {
    return <Skeleton className="h-[100px] w-full" />;
  }

  if (!quota) return null;

  const percent = Math.min(quota.usage_percent, 100);

  return (
    <Card
      className="cursor-pointer hover:shadow-[var(--shadow-lg)] transition-shadow"
      onClick={() => router.push('/billing')}
    >
      <CardContent className="p-4">
        <div className="flex justify-between mb-2">
          <span className="text-sm font-medium text-[var(--text-high)]">
            Usage ({quota.plan.display_name})
          </span>
          <span className="text-sm text-[var(--text-mid)]">
            {percent.toFixed(0)}%
          </span>
        </div>
        <Progress
          value={percent}
          className={`h-1.5 ${
            percent >= 100
              ? '[&>div]:bg-red-500'
              : percent >= 80
              ? '[&>div]:bg-amber-500'
              : ''
          }`}
        />
      </CardContent>
    </Card>
  );
}
