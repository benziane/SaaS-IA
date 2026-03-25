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
  IconButton,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  MenuItem,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import PaletteIcon from '@mui/icons-material/Palette';
import { useState } from 'react';

import {
  useCreateTenant,
  useTenants,
  useUpdateBranding,
  useUpdateTenant,
} from '@/features/tenants/hooks/useTenants';
import type {
  BrandingUpdateRequest,
  Tenant,
  TenantCreateRequest,
  TenantUpdateRequest,
} from '@/features/tenants/types';
import { extractErrorMessage } from '@/lib/apiClient';

const PLAN_OPTIONS = ['free', 'pro', 'enterprise'] as const;

function PlanChip({ plan }: { plan: string }) {
  const colorMap: Record<string, 'default' | 'primary' | 'secondary'> = {
    free: 'default',
    pro: 'primary',
    enterprise: 'secondary',
  };
  return (
    <Chip
      label={plan.charAt(0).toUpperCase() + plan.slice(1)}
      color={colorMap[plan] || 'default'}
      size="small"
    />
  );
}

function StatusChip({ active }: { active: boolean }) {
  return (
    <Chip
      label={active ? 'Active' : 'Inactive'}
      color={active ? 'success' : 'error'}
      size="small"
      variant="outlined"
    />
  );
}

function CreateTenantDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const createMutation = useCreateTenant();
  const [form, setForm] = useState<TenantCreateRequest>({
    name: '',
    slug: '',
    plan: 'free',
    max_users: 5,
    max_storage_mb: 1000,
  });
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);
    try {
      await createMutation.mutateAsync(form);
      setForm({ name: '', slug: '', plan: 'free', max_users: 5, max_storage_mb: 1000 });
      onClose();
    } catch (e) {
      setError(extractErrorMessage(e));
    }
  };

  const handleNameChange = (name: string) => {
    const slug = name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
    setForm((prev) => ({ ...prev, name, slug }));
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Tenant</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <TextField
          label="Organization Name"
          fullWidth
          required
          margin="normal"
          value={form.name}
          onChange={(e) => handleNameChange(e.target.value)}
        />
        <TextField
          label="Slug"
          fullWidth
          required
          margin="normal"
          value={form.slug}
          onChange={(e) => setForm((prev) => ({ ...prev, slug: e.target.value }))}
          helperText="URL-friendly identifier (lowercase, hyphens allowed)"
        />
        <TextField
          label="Plan"
          fullWidth
          select
          margin="normal"
          value={form.plan}
          onChange={(e) =>
            setForm((prev) => ({
              ...prev,
              plan: e.target.value as TenantCreateRequest['plan'],
            }))
          }
        >
          {PLAN_OPTIONS.map((p) => (
            <MenuItem key={p} value={p}>
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </MenuItem>
          ))}
        </TextField>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <TextField
              label="Max Users"
              type="number"
              fullWidth
              margin="normal"
              value={form.max_users}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  max_users: parseInt(e.target.value, 10) || 5,
                }))
              }
              inputProps={{ min: 1, max: 10000 }}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              label="Max Storage (MB)"
              type="number"
              fullWidth
              margin="normal"
              value={form.max_storage_mb}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  max_storage_mb: parseInt(e.target.value, 10) || 1000,
                }))
              }
              inputProps={{ min: 100, max: 1000000 }}
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={createMutation.isPending || !form.name || !form.slug}
        >
          {createMutation.isPending ? 'Creating...' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function EditTenantDialog({
  tenant,
  onClose,
}: {
  tenant: Tenant | null;
  onClose: () => void;
}) {
  const updateMutation = useUpdateTenant();
  const [form, setForm] = useState<TenantUpdateRequest>({});
  const [error, setError] = useState<string | null>(null);

  const handleOpen = () => {
    if (tenant) {
      setForm({
        name: tenant.name,
        plan: tenant.plan as TenantUpdateRequest['plan'],
        is_active: tenant.is_active,
        max_users: tenant.max_users,
        max_storage_mb: tenant.max_storage_mb,
      });
    }
  };

  // biome-ignore lint: intentional
  useState(() => {
    handleOpen();
  });

  const handleSubmit = async () => {
    if (!tenant) return;
    setError(null);
    try {
      await updateMutation.mutateAsync({ tenantId: tenant.id, data: form });
      onClose();
    } catch (e) {
      setError(extractErrorMessage(e));
    }
  };

  if (!tenant) return null;

  return (
    <Dialog open={!!tenant} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Edit Tenant: {tenant.name}</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <TextField
          label="Organization Name"
          fullWidth
          margin="normal"
          value={form.name || ''}
          onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
        />
        <TextField
          label="Plan"
          fullWidth
          select
          margin="normal"
          value={form.plan || tenant.plan}
          onChange={(e) =>
            setForm((prev) => ({
              ...prev,
              plan: e.target.value as TenantUpdateRequest['plan'],
            }))
          }
        >
          {PLAN_OPTIONS.map((p) => (
            <MenuItem key={p} value={p}>
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          label="Status"
          fullWidth
          select
          margin="normal"
          value={form.is_active !== undefined ? String(form.is_active) : 'true'}
          onChange={(e) =>
            setForm((prev) => ({ ...prev, is_active: e.target.value === 'true' }))
          }
        >
          <MenuItem value="true">Active</MenuItem>
          <MenuItem value="false">Inactive</MenuItem>
        </TextField>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <TextField
              label="Max Users"
              type="number"
              fullWidth
              margin="normal"
              value={form.max_users ?? tenant.max_users}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  max_users: parseInt(e.target.value, 10) || 5,
                }))
              }
              inputProps={{ min: 1, max: 10000 }}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              label="Max Storage (MB)"
              type="number"
              fullWidth
              margin="normal"
              value={form.max_storage_mb ?? tenant.max_storage_mb}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  max_storage_mb: parseInt(e.target.value, 10) || 1000,
                }))
              }
              inputProps={{ min: 100, max: 1000000 }}
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={updateMutation.isPending}
        >
          {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function BrandingDialog({
  tenant,
  onClose,
}: {
  tenant: Tenant | null;
  onClose: () => void;
}) {
  const brandingMutation = useUpdateBranding();
  const [form, setForm] = useState<BrandingUpdateRequest>({});
  const [error, setError] = useState<string | null>(null);

  // biome-ignore lint: intentional
  useState(() => {
    if (tenant) {
      setForm({
        logo_url: tenant.branding?.logo_url || '',
        primary_color: tenant.branding?.primary_color || '#1976d2',
        favicon: tenant.branding?.favicon || '',
        custom_domain: tenant.branding?.custom_domain || '',
      });
    }
  });

  const handleSubmit = async () => {
    if (!tenant) return;
    setError(null);
    try {
      await brandingMutation.mutateAsync({ tenantId: tenant.id, data: form });
      onClose();
    } catch (e) {
      setError(extractErrorMessage(e));
    }
  };

  if (!tenant) return null;

  return (
    <Dialog open={!!tenant} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Branding: {tenant.name}</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <TextField
          label="Logo URL"
          fullWidth
          margin="normal"
          value={form.logo_url || ''}
          onChange={(e) => setForm((prev) => ({ ...prev, logo_url: e.target.value }))}
          placeholder="https://cdn.example.com/logo.png"
        />
        <TextField
          label="Primary Color"
          fullWidth
          margin="normal"
          value={form.primary_color || ''}
          onChange={(e) =>
            setForm((prev) => ({ ...prev, primary_color: e.target.value }))
          }
          placeholder="#1976d2"
          helperText="Hex color code (e.g., #1976d2)"
        />
        <TextField
          label="Favicon URL"
          fullWidth
          margin="normal"
          value={form.favicon || ''}
          onChange={(e) => setForm((prev) => ({ ...prev, favicon: e.target.value }))}
          placeholder="https://cdn.example.com/favicon.ico"
        />
        <TextField
          label="Custom Domain"
          fullWidth
          margin="normal"
          value={form.custom_domain || ''}
          onChange={(e) =>
            setForm((prev) => ({ ...prev, custom_domain: e.target.value }))
          }
          placeholder="app.yourcompany.com"
          helperText="Custom domain for white-label access"
        />
        {form.primary_color && /^#[0-9a-fA-F]{6}$/.test(form.primary_color) && (
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Preview:
            </Typography>
            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: 1,
                backgroundColor: form.primary_color,
                border: '1px solid',
                borderColor: 'divider',
              }}
            />
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={brandingMutation.isPending}
        >
          {brandingMutation.isPending ? 'Saving...' : 'Save Branding'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default function TenantsPage() {
  const { data, isLoading, error } = useTenants();
  const [createOpen, setCreateOpen] = useState(false);
  const [editTenant, setEditTenant] = useState<Tenant | null>(null);
  const [brandingTenant, setBrandingTenant] = useState<Tenant | null>(null);

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Skeleton variant="text" width={300} height={40} sx={{ mb: 2 }} />
        <Skeleton variant="rectangular" height={400} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load tenants. You may not have admin access.
        </Alert>
      </Box>
    );
  }

  const tenants = data?.tenants || [];

  return (
    <Box sx={{ p: 3 }}>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3,
        }}
      >
        <Box>
          <Typography variant="h4">Tenant Management</Typography>
          <Typography variant="body2" color="text.secondary">
            {data?.count || 0} organization{(data?.count || 0) !== 1 ? 's' : ''} registered
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
        >
          New Tenant
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="h3" color="primary">
                {tenants.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Tenants
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="h3" color="success.main">
                {tenants.filter((t) => t.is_active).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="h3" color="secondary">
                {tenants.filter((t) => t.plan === 'enterprise').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Enterprise
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tenants Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Organization</TableCell>
                <TableCell>Slug</TableCell>
                <TableCell>Plan</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Max Users</TableCell>
                <TableCell align="right">Storage (MB)</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tenants.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                      No tenants yet. Create your first organization to get started.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                tenants.map((tenant) => (
                  <TableRow key={tenant.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>
                        {tenant.name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace" color="text.secondary">
                        {tenant.slug}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <PlanChip plan={tenant.plan} />
                    </TableCell>
                    <TableCell>
                      <StatusChip active={tenant.is_active} />
                    </TableCell>
                    <TableCell align="right">{tenant.max_users}</TableCell>
                    <TableCell align="right">
                      {tenant.max_storage_mb.toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {new Date(tenant.created_at).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => setEditTenant(tenant)}
                        title="Edit tenant"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => setBrandingTenant(tenant)}
                        title="Edit branding"
                      >
                        <PaletteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Dialogs */}
      <CreateTenantDialog open={createOpen} onClose={() => setCreateOpen(false)} />
      {editTenant && (
        <EditTenantDialog tenant={editTenant} onClose={() => setEditTenant(null)} />
      )}
      {brandingTenant && (
        <BrandingDialog
          tenant={brandingTenant}
          onClose={() => setBrandingTenant(null)}
        />
      )}
    </Box>
  );
}
