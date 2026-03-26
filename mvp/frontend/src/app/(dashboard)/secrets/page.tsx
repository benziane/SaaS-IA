'use client';

import { useState } from 'react';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/lib/design-hub/components/Select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
} from '@/lib/design-hub/components/Dialog';

import {
  useCompleteRotation,
  useMarkCompromised,
  useRegisterSecret,
  useSecretAlerts,
  useSecretHealth,
  useSecrets,
  useStartRotation,
} from '@/features/secrets/hooks/useSecrets';
import type { SecretRegistration } from '@/features/secrets/types';

function HealthScore({ score }: { score: number }) {
  let colorClass = 'text-green-400';
  let progressColor = 'success';
  if (score < 70) { colorClass = 'text-red-400'; progressColor = 'error'; }
  else if (score < 90) { colorClass = 'text-amber-400'; progressColor = 'warning'; }

  return (
    <div className="text-center">
      <p className={`text-5xl font-bold ${colorClass}`}>
        {score}
      </p>
      <p className="text-sm text-[var(--text-mid)]">
        Health Score
      </p>
      <Progress
        value={score}
        className={`h-2 mt-2 ${
          progressColor === 'error' ? '[&>div]:bg-red-500' :
          progressColor === 'warning' ? '[&>div]:bg-amber-500' :
          '[&>div]:bg-green-500'
        }`}
      />
    </div>
  );
}

function StatusChip({ status }: { status: string }) {
  const colorMap: Record<string, 'success' | 'default' | 'warning' | 'destructive'> = {
    active: 'success',
    rotating: 'default',
    expired: 'warning',
    compromised: 'destructive',
  };
  return (
    <Badge variant={colorMap[status] ?? 'secondary'}>
      {status.toUpperCase()}
    </Badge>
  );
}

function UrgencyChip({ urgency }: { urgency: string }) {
  const colorMap: Record<string, 'destructive' | 'warning' | 'default'> = {
    critical: 'destructive',
    overdue: 'destructive',
    warning: 'warning',
  };
  return (
    <Badge variant={colorMap[urgency] ?? 'outline'}>
      {urgency.toUpperCase()}
    </Badge>
  );
}

function formatDate(iso: string | null): string {
  if (!iso) return '--';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function RegisterDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [name, setName] = useState('');
  const [secretType, setSecretType] = useState('api_key');
  const [rotationDays, setRotationDays] = useState(90);
  const [notes, setNotes] = useState('');
  const registerMutation = useRegisterSecret();

  const handleSubmit = () => {
    registerMutation.mutate(
      { name, secret_type: secretType, rotation_days: rotationDays, notes: notes || undefined },
      {
        onSuccess: () => {
          setName('');
          setSecretType('api_key');
          setRotationDays(90);
          setNotes('');
          onClose();
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Register Secret for Tracking</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <p className="text-sm text-[var(--text-mid)]">
            This only registers metadata for rotation tracking. The actual secret value is never
            stored.
          </p>
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Environment Variable Name</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. MY_API_KEY"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Secret Type</label>
            <Select value={secretType} onValueChange={setSecretType}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="api_key">API Key</SelectItem>
                <SelectItem value="database">Database</SelectItem>
                <SelectItem value="jwt">JWT</SelectItem>
                <SelectItem value="webhook">Webhook</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Rotation Period (days)</label>
            <Input
              type="number"
              value={rotationDays}
              onChange={(e) => setRotationDays(Number(e.target.value))}
              min={1}
              max={730}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Notes (optional)</label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            disabled={!name || registerMutation.isPending}
          >
            {registerMutation.isPending ? 'Registering...' : 'Register'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function SecretActionsCell({ secret }: { secret: SecretRegistration }) {
  const startMutation = useStartRotation();
  const completeMutation = useCompleteRotation();
  const compromisedMutation = useMarkCompromised();

  if (secret.status === 'compromised') {
    return (
      <Button
        size="sm"
        variant="outline"
        className="text-amber-400 border-amber-400/30"
        onClick={() => startMutation.mutate({ name: secret.name })}
        disabled={startMutation.isPending}
      >
        Start Rotation
      </Button>
    );
  }

  if (secret.status === 'rotating') {
    return (
      <Button
        size="sm"
        className="bg-green-600 hover:bg-green-700 text-white"
        onClick={() => completeMutation.mutate(secret.name)}
        disabled={completeMutation.isPending}
      >
        Complete Rotation
      </Button>
    );
  }

  return (
    <div className="flex gap-2">
      <Button
        size="sm"
        variant="outline"
        onClick={() => startMutation.mutate({ name: secret.name })}
        disabled={startMutation.isPending}
      >
        Rotate
      </Button>
      <Button
        size="sm"
        variant="outline"
        className="text-red-400 border-red-400/30 hover:bg-red-400/10"
        onClick={() => {
          if (window.confirm(`Mark "${secret.name}" as COMPROMISED? This triggers an urgent alert.`)) {
            compromisedMutation.mutate(secret.name);
          }
        }}
        disabled={compromisedMutation.isPending}
      >
        Compromised
      </Button>
    </div>
  );
}

export default function SecretsPage() {
  const [registerOpen, setRegisterOpen] = useState(false);
  const { data: secrets, isLoading: secretsLoading, error: secretsError } = useSecrets();
  const { data: alerts, isLoading: alertsLoading } = useSecretAlerts();
  const { data: health, isLoading: healthLoading } = useSecretHealth();

  if (secretsLoading || alertsLoading || healthLoading) {
    return (
      <div className="p-6">
        <Skeleton className="w-72 h-10 mb-4" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-[100px]" />
          ))}
        </div>
        <Skeleton className="h-[300px]" />
      </div>
    );
  }

  if (secretsError) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load secrets data. You may need admin privileges.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-[var(--text-high)]">Secrets Rotation Manager</h1>
        <Button onClick={() => setRegisterOpen(true)}>
          Register Secret
        </Button>
      </div>

      {/* Health Score + Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <Card className="md:col-span-1">
          <CardContent className="p-6">
            {health && <HealthScore score={health.score} />}
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-4xl font-bold text-[var(--text-high)]">{health?.total ?? 0}</p>
            <p className="text-sm text-[var(--text-mid)]">Total Tracked</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-4xl font-bold text-green-400">{health?.healthy ?? 0}</p>
            <p className="text-sm text-[var(--text-mid)]">Healthy</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-4xl font-bold text-amber-400">{health?.warning ?? 0}</p>
            <p className="text-sm text-[var(--text-mid)]">Warning</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-4xl font-bold text-red-400">
              {(health?.overdue ?? 0) + (health?.compromised ?? 0)}
            </p>
            <p className="text-sm text-[var(--text-mid)]">
              Overdue / Compromised
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      {alerts && alerts.length > 0 && (
        <div className="mb-6 space-y-2">
          {alerts.map((alert, idx) => (
            <Alert
              key={idx}
              variant={alert.urgency === 'critical' || alert.urgency === 'overdue' ? 'destructive' : 'warning'}
            >
              <div className="flex justify-between items-center">
                <AlertDescription>{alert.message}</AlertDescription>
                <UrgencyChip urgency={alert.urgency} />
              </div>
            </Alert>
          ))}
        </div>
      )}

      {/* Secrets Table */}
      <Card>
        <CardContent className="p-6">
          <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">
            Registered Secrets
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  <th className="text-left py-2 px-3 font-medium text-[var(--text-mid)]">Name</th>
                  <th className="text-left py-2 px-3 font-medium text-[var(--text-mid)]">Type</th>
                  <th className="text-left py-2 px-3 font-medium text-[var(--text-mid)]">Status</th>
                  <th className="text-right py-2 px-3 font-medium text-[var(--text-mid)]">Age (days)</th>
                  <th className="text-right py-2 px-3 font-medium text-[var(--text-mid)]">Rotation Period</th>
                  <th className="text-left py-2 px-3 font-medium text-[var(--text-mid)]">Last Rotated</th>
                  <th className="text-left py-2 px-3 font-medium text-[var(--text-mid)]">Next Rotation</th>
                  <th className="text-right py-2 px-3 font-medium text-[var(--text-mid)]">Rotations</th>
                  <th className="text-left py-2 px-3 font-medium text-[var(--text-mid)]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {secrets?.map((secret) => {
                  const isOverdue =
                    secret.next_rotation_at &&
                    new Date(secret.next_rotation_at) < new Date();
                  return (
                    <tr
                      key={secret.id}
                      className={`border-b border-[var(--border)] ${
                        secret.status === 'compromised'
                          ? 'bg-red-500/5'
                          : isOverdue
                          ? 'bg-amber-500/5'
                          : ''
                      }`}
                    >
                      <td className="py-2 px-3">
                        <span className="font-semibold font-mono text-[var(--text-high)]">
                          {secret.name}
                        </span>
                      </td>
                      <td className="py-2 px-3">
                        <Badge variant="outline" className="text-xs">{secret.secret_type}</Badge>
                      </td>
                      <td className="py-2 px-3">
                        <StatusChip status={secret.status} />
                      </td>
                      <td className="py-2 px-3 text-right text-[var(--text-high)]">{secret.age_days}</td>
                      <td className="py-2 px-3 text-right text-[var(--text-high)]">{secret.rotation_days}d</td>
                      <td className="py-2 px-3 text-[var(--text-mid)]">{formatDate(secret.last_rotated_at)}</td>
                      <td className="py-2 px-3 text-[var(--text-mid)]">{formatDate(secret.next_rotation_at)}</td>
                      <td className="py-2 px-3 text-right text-[var(--text-high)]">{secret.rotation_count}</td>
                      <td className="py-2 px-3">
                        <SecretActionsCell secret={secret} />
                      </td>
                    </tr>
                  );
                })}
                {(!secrets || secrets.length === 0) && (
                  <tr>
                    <td colSpan={9} className="text-center py-6">
                      <p className="text-[var(--text-mid)]">
                        No secrets registered. Click &quot;Register Secret&quot; to start tracking.
                      </p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <RegisterDialog open={registerOpen} onClose={() => setRegisterOpen(false)} />
    </div>
  );
}
