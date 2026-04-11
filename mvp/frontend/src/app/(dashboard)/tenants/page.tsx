'use client';

import { useState } from 'react';
import { Plus, Pencil, Palette, Building2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
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
  const colorMap: Record<string, 'secondary' | 'default' | 'warning'> = {
    free: 'secondary',
    pro: 'default',
    enterprise: 'warning',
  };
  return (
    <Badge variant={colorMap[plan] || 'secondary'}>
      {plan.charAt(0).toUpperCase() + plan.slice(1)}
    </Badge>
  );
}

function StatusChip({ active }: { active: boolean }) {
  return (
    <Badge variant={active ? 'success' : 'destructive'}>
      {active ? 'Active' : 'Inactive'}
    </Badge>
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
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Tenant</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Organization Name</label>
            <Input
              value={form.name}
              onChange={(e) => handleNameChange(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Slug</label>
            <Input
              value={form.slug}
              onChange={(e) => setForm((prev) => ({ ...prev, slug: e.target.value }))}
              required
            />
            <p className="text-xs text-[var(--text-low)] mt-1">URL-friendly identifier (lowercase, hyphens allowed)</p>
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Plan</label>
            <Select
              value={form.plan}
              onValueChange={(v) => setForm((prev) => ({ ...prev, plan: v as TenantCreateRequest['plan'] }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PLAN_OPTIONS.map((p) => (
                  <SelectItem key={p} value={p}>
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Max Users</label>
              <Input
                type="number"
                value={form.max_users}
                onChange={(e) => setForm((prev) => ({ ...prev, max_users: parseInt(e.target.value, 10) || 5 }))}
                min={1}
                max={10000}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Max Storage (MB)</label>
              <Input
                type="number"
                value={form.max_storage_mb}
                onChange={(e) => setForm((prev) => ({ ...prev, max_storage_mb: parseInt(e.target.value, 10) || 1000 }))}
                min={100}
                max={1000000}
              />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            disabled={createMutation.isPending || !form.name || !form.slug}
          >
            {createMutation.isPending ? 'Creating...' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
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
    <Dialog open={!!tenant} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Tenant: {tenant.name}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Organization Name</label>
            <Input
              value={form.name || ''}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Plan</label>
            <Select
              value={form.plan || tenant.plan}
              onValueChange={(v) => setForm((prev) => ({ ...prev, plan: v as TenantUpdateRequest['plan'] }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PLAN_OPTIONS.map((p) => (
                  <SelectItem key={p} value={p}>
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Status</label>
            <Select
              value={form.is_active !== undefined ? String(form.is_active) : 'true'}
              onValueChange={(v) => setForm((prev) => ({ ...prev, is_active: v === 'true' }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="true">Active</SelectItem>
                <SelectItem value="false">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Max Users</label>
              <Input
                type="number"
                value={form.max_users ?? tenant.max_users}
                onChange={(e) => setForm((prev) => ({ ...prev, max_users: parseInt(e.target.value, 10) || 5 }))}
                min={1}
                max={10000}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Max Storage (MB)</label>
              <Input
                type="number"
                value={form.max_storage_mb ?? tenant.max_storage_mb}
                onChange={(e) => setForm((prev) => ({ ...prev, max_storage_mb: parseInt(e.target.value, 10) || 1000 }))}
                min={100}
                max={1000000}
              />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
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
    <Dialog open={!!tenant} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Branding: {tenant.name}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Logo URL</label>
            <Input
              value={form.logo_url || ''}
              onChange={(e) => setForm((prev) => ({ ...prev, logo_url: e.target.value }))}
              placeholder="https://cdn.example.com/logo.png"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Primary Color</label>
            <Input
              value={form.primary_color || ''}
              onChange={(e) => setForm((prev) => ({ ...prev, primary_color: e.target.value }))}
              placeholder="#1976d2"
            />
            <p className="text-xs text-[var(--text-low)] mt-1">Hex color code (e.g., #1976d2)</p>
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Favicon URL</label>
            <Input
              value={form.favicon || ''}
              onChange={(e) => setForm((prev) => ({ ...prev, favicon: e.target.value }))}
              placeholder="https://cdn.example.com/favicon.ico"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Custom Domain</label>
            <Input
              value={form.custom_domain || ''}
              onChange={(e) => setForm((prev) => ({ ...prev, custom_domain: e.target.value }))}
              placeholder="app.yourcompany.com"
            />
            <p className="text-xs text-[var(--text-low)] mt-1">Custom domain for white-label access</p>
          </div>
          {form.primary_color && /^#[0-9a-fA-F]{6}$/.test(form.primary_color) && (
            <div className="flex items-center gap-4">
              <span className="text-sm text-[var(--text-mid)]">Preview:</span>
              <div
                className="w-10 h-10 rounded border border-[var(--border)]"
                style={{ backgroundColor: form.primary_color }}
              />
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            disabled={brandingMutation.isPending}
          >
            {brandingMutation.isPending ? 'Saving...' : 'Save Branding'}
          </Button>
        </DialogFooter>
      </DialogContent>
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
      <div className="p-5">
        <Skeleton className="w-72 h-10 mb-4" />
        <Skeleton className="h-[400px]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-5">
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load tenants. You may not have admin access.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const tenants = data?.tenants || [];

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
            <Building2 className="h-5 w-5 text-[var(--accent)]" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">Tenant Management</h1>
            <p className="text-xs text-[var(--text-mid)]">Multi-tenant isolation and management</p>
          </div>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-1" /> New Tenant
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="surface-card p-5">
          <p className="text-4xl font-bold text-[var(--accent)]">{tenants.length}</p>
          <p className="text-sm text-[var(--text-mid)]">Total Tenants</p>
        </div>
        <div className="surface-card p-5">
          <p className="text-4xl font-bold text-green-400">
            {tenants.filter((t) => t.is_active).length}
          </p>
          <p className="text-sm text-[var(--text-mid)]">Active</p>
        </div>
        <div className="surface-card p-5">
          <p className="text-4xl font-bold text-purple-400">
            {tenants.filter((t) => t.plan === 'enterprise').length}
          </p>
          <p className="text-sm text-[var(--text-mid)]">Enterprise</p>
        </div>
      </div>

      {/* Tenants Table */}
      <div className="surface-card p-5">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border)]">
                <th className="text-left py-3 px-4 font-medium text-[var(--text-mid)]">Organization</th>
                <th className="text-left py-3 px-4 font-medium text-[var(--text-mid)]">Slug</th>
                <th className="text-left py-3 px-4 font-medium text-[var(--text-mid)]">Plan</th>
                <th className="text-left py-3 px-4 font-medium text-[var(--text-mid)]">Status</th>
                <th className="text-right py-3 px-4 font-medium text-[var(--text-mid)]">Max Users</th>
                <th className="text-right py-3 px-4 font-medium text-[var(--text-mid)]">Storage (MB)</th>
                <th className="text-left py-3 px-4 font-medium text-[var(--text-mid)]">Created</th>
                <th className="text-center py-3 px-4 font-medium text-[var(--text-mid)]">Actions</th>
              </tr>
            </thead>
            <tbody>
              {tenants.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-8">
                    <p className="text-[var(--text-mid)]">
                      No tenants yet. Create your first organization to get started.
                    </p>
                  </td>
                </tr>
              ) : (
                tenants.map((tenant) => (
                  <tr key={tenant.id} className="border-b border-[var(--border)] hover:bg-[var(--bg-elevated)] transition-colors">
                    <td className="py-3 px-4">
                      <span className="font-semibold text-[var(--text-high)]">{tenant.name}</span>
                    </td>
                    <td className="py-3 px-4">
                      <code className="font-mono text-[var(--text-mid)]">{tenant.slug}</code>
                    </td>
                    <td className="py-3 px-4">
                      <PlanChip plan={tenant.plan} />
                    </td>
                    <td className="py-3 px-4">
                      <StatusChip active={tenant.is_active} />
                    </td>
                    <td className="py-3 px-4 text-right text-[var(--text-high)]">{tenant.max_users}</td>
                    <td className="py-3 px-4 text-right text-[var(--text-high)]">
                      {tenant.max_storage_mb.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-[var(--text-mid)]">
                      {new Date(tenant.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        type="button"
                        className="p-1.5 rounded hover:bg-[var(--bg-elevated)] text-[var(--text-mid)] hover:text-[var(--text-high)] transition-colors inline-block"
                        onClick={() => setEditTenant(tenant)}
                        title="Edit tenant"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        className="p-1.5 rounded hover:bg-[var(--bg-elevated)] text-[var(--text-mid)] hover:text-[var(--text-high)] transition-colors inline-block"
                        onClick={() => setBrandingTenant(tenant)}
                        title="Edit branding"
                      >
                        <Palette className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

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
    </div>
  );
}
