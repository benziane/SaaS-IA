'use client';

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  LinearProgress,
  MenuItem,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';

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
  let color: 'success' | 'warning' | 'error' = 'success';
  if (score < 70) color = 'error';
  else if (score < 90) color = 'warning';

  return (
    <Box sx={{ textAlign: 'center' }}>
      <Typography variant="h2" color={`${color}.main`} fontWeight={700}>
        {score}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Health Score
      </Typography>
      <LinearProgress
        variant="determinate"
        value={score}
        color={color}
        sx={{ height: 8, borderRadius: 4, mt: 1 }}
      />
    </Box>
  );
}

function StatusChip({ status }: { status: string }) {
  const colorMap: Record<string, 'success' | 'warning' | 'error' | 'info'> = {
    active: 'success',
    rotating: 'info',
    expired: 'warning',
    compromised: 'error',
  };
  return (
    <Chip
      label={status.toUpperCase()}
      color={colorMap[status] ?? 'default'}
      size="small"
      variant="filled"
    />
  );
}

function UrgencyChip({ urgency }: { urgency: string }) {
  const colorMap: Record<string, 'error' | 'warning' | 'info'> = {
    critical: 'error',
    overdue: 'error',
    warning: 'warning',
  };
  return (
    <Chip
      label={urgency.toUpperCase()}
      color={colorMap[urgency] ?? 'info'}
      size="small"
      variant="outlined"
    />
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
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Register Secret for Tracking</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          This only registers metadata for rotation tracking. The actual secret value is never
          stored.
        </Typography>
        <TextField
          label="Environment Variable Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          fullWidth
          margin="normal"
          placeholder="e.g. MY_API_KEY"
          required
        />
        <TextField
          label="Secret Type"
          value={secretType}
          onChange={(e) => setSecretType(e.target.value)}
          select
          fullWidth
          margin="normal"
        >
          <MenuItem value="api_key">API Key</MenuItem>
          <MenuItem value="database">Database</MenuItem>
          <MenuItem value="jwt">JWT</MenuItem>
          <MenuItem value="webhook">Webhook</MenuItem>
          <MenuItem value="other">Other</MenuItem>
        </TextField>
        <TextField
          label="Rotation Period (days)"
          type="number"
          value={rotationDays}
          onChange={(e) => setRotationDays(Number(e.target.value))}
          fullWidth
          margin="normal"
          inputProps={{ min: 1, max: 730 }}
        />
        <TextField
          label="Notes (optional)"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          fullWidth
          margin="normal"
          multiline
          rows={2}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!name || registerMutation.isPending}
        >
          {registerMutation.isPending ? 'Registering...' : 'Register'}
        </Button>
      </DialogActions>
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
        size="small"
        variant="outlined"
        color="warning"
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
        size="small"
        variant="contained"
        color="success"
        onClick={() => completeMutation.mutate(secret.name)}
        disabled={completeMutation.isPending}
      >
        Complete Rotation
      </Button>
    );
  }

  return (
    <Box sx={{ display: 'flex', gap: 1 }}>
      <Button
        size="small"
        variant="outlined"
        onClick={() => startMutation.mutate({ name: secret.name })}
        disabled={startMutation.isPending}
      >
        Rotate
      </Button>
      <Button
        size="small"
        variant="outlined"
        color="error"
        onClick={() => {
          if (window.confirm(`Mark "${secret.name}" as COMPROMISED? This triggers an urgent alert.`)) {
            compromisedMutation.mutate(secret.name);
          }
        }}
        disabled={compromisedMutation.isPending}
      >
        Compromised
      </Button>
    </Box>
  );
}

export default function SecretsPage() {
  const [registerOpen, setRegisterOpen] = useState(false);
  const { data: secrets, isLoading: secretsLoading, error: secretsError } = useSecrets();
  const { data: alerts, isLoading: alertsLoading } = useSecretAlerts();
  const { data: health, isLoading: healthLoading } = useSecretHealth();

  if (secretsLoading || alertsLoading || healthLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Skeleton variant="text" width={300} height={40} sx={{ mb: 2 }} />
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {[1, 2, 3, 4].map((i) => (
            <Grid item xs={6} md={3} key={i}>
              <Skeleton variant="rectangular" height={100} />
            </Grid>
          ))}
        </Grid>
        <Skeleton variant="rectangular" height={300} />
      </Box>
    );
  }

  if (secretsError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load secrets data. You may need admin privileges.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Secrets Rotation Manager</Typography>
        <Button variant="contained" onClick={() => setRegisterOpen(true)}>
          Register Secret
        </Button>
      </Box>

      {/* Health Score + Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              {health && <HealthScore score={health.score} />}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="text.primary">{health?.total ?? 0}</Typography>
              <Typography variant="body2" color="text.secondary">Total Tracked</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="success.main">{health?.healthy ?? 0}</Typography>
              <Typography variant="body2" color="text.secondary">Healthy</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={2}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="warning.main">{health?.warning ?? 0}</Typography>
              <Typography variant="body2" color="text.secondary">Warning</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="error.main">
                {(health?.overdue ?? 0) + (health?.compromised ?? 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Overdue / Compromised
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts */}
      {alerts && alerts.length > 0 && (
        <Box sx={{ mb: 3 }}>
          {alerts.map((alert, idx) => (
            <Alert
              key={idx}
              severity={alert.urgency === 'critical' || alert.urgency === 'overdue' ? 'error' : 'warning'}
              sx={{ mb: 1 }}
              action={
                <UrgencyChip urgency={alert.urgency} />
              }
            >
              {alert.message}
            </Alert>
          ))}
        </Box>
      )}

      {/* Secrets Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Registered Secrets
          </Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Age (days)</TableCell>
                  <TableCell align="right">Rotation Period</TableCell>
                  <TableCell>Last Rotated</TableCell>
                  <TableCell>Next Rotation</TableCell>
                  <TableCell align="right">Rotations</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {secrets?.map((secret) => {
                  const isOverdue =
                    secret.next_rotation_at &&
                    new Date(secret.next_rotation_at) < new Date();
                  return (
                    <TableRow
                      key={secret.id}
                      sx={{
                        bgcolor:
                          secret.status === 'compromised'
                            ? 'error.50'
                            : isOverdue
                            ? 'warning.50'
                            : undefined,
                      }}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight={600} fontFamily="monospace">
                          {secret.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={secret.secret_type} size="small" variant="outlined" />
                      </TableCell>
                      <TableCell>
                        <StatusChip status={secret.status} />
                      </TableCell>
                      <TableCell align="right">{secret.age_days}</TableCell>
                      <TableCell align="right">{secret.rotation_days}d</TableCell>
                      <TableCell>{formatDate(secret.last_rotated_at)}</TableCell>
                      <TableCell>{formatDate(secret.next_rotation_at)}</TableCell>
                      <TableCell align="right">{secret.rotation_count}</TableCell>
                      <TableCell>
                        <SecretActionsCell secret={secret} />
                      </TableCell>
                    </TableRow>
                  );
                })}
                {(!secrets || secrets.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      <Typography color="text.secondary" sx={{ py: 3 }}>
                        No secrets registered. Click "Register Secret" to start tracking.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <RegisterDialog open={registerOpen} onClose={() => setRegisterOpen(false)} />
    </Box>
  );
}
