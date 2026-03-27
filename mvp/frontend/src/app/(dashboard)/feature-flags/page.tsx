'use client';

import { useEffect, useMemo, useState } from 'react';
import { Flag, Search, PowerOff, RotateCcw, Trash2, Users, Percent, ToggleLeft, Loader2 } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Switch } from '@/lib/design-hub/components/Switch';
import { Separator } from '@/lib/design-hub/components/Separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/lib/design-hub/components/Select';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/lib/design-hub/components/Tooltip';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
} from '@/lib/design-hub/components/Dialog';

import {
  useFeatureFlags,
  useSetFeatureFlag,
  useDeleteFeatureFlag,
  useKillModule,
  useRestoreModule,
} from '@/features/feature-flags/hooks/useFeatureFlags';
import type { FeatureFlag } from '@/features/feature-flags/types';

type FlagCategory = 'all' | 'modules' | 'enterprise' | 'overridden';

function getFlagType(flag: FeatureFlag): 'boolean' | 'percentage' | 'whitelist' | 'default' {
  if (flag.override === null) return 'default';
  if (flag.override === 'true' || flag.override === 'false') return 'boolean';
  if (typeof flag.override === 'string' && flag.override.endsWith('%')) return 'percentage';
  if (typeof flag.override === 'string' && flag.override.startsWith('users:')) return 'whitelist';
  return 'boolean';
}

function getModuleName(flagName: string): string | null {
  if (flagName.endsWith('_enabled')) {
    return flagName.replace('_enabled', '');
  }
  return null;
}

function isEffectivelyEnabled(flag: FeatureFlag): boolean {
  if (flag.effective === true || flag.effective === 'true') return true;
  if (flag.effective === false || flag.effective === 'false') return false;
  return true;
}

export default function FeatureFlagsPage() {
  const { data, isLoading, error } = useFeatureFlags();
  const setFlagMutation = useSetFeatureFlag();
  const deleteFlagMutation = useDeleteFeatureFlag();
  const killMutation = useKillModule();
  const restoreMutation = useRestoreModule();

  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<FlagCategory>('all');
  const [editDialog, setEditDialog] = useState<{ open: boolean; flag: FeatureFlag | null }>({
    open: false,
    flag: null,
  });
  const [editMode, setEditMode] = useState<'boolean' | 'percentage' | 'whitelist'>('boolean');
  const [editValue, setEditValue] = useState('');
  const [percentValue, setPercentValue] = useState(50);
  const [whitelistValue, setWhitelistValue] = useState('');
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  // Auto-dismiss snackbar after 4 seconds
  useEffect(() => {
    if (!snackbar.open) return;
    const timer = setTimeout(() => setSnackbar((s) => ({ ...s, open: false })), 4000);
    return () => clearTimeout(timer);
  }, [snackbar.open]);

  const flags = useMemo(() => {
    if (!data?.flags) return [];
    let entries = Object.values(data.flags);

    if (search) {
      const s = search.toLowerCase();
      entries = entries.filter((f) => f.name.toLowerCase().includes(s));
    }

    if (category === 'modules') {
      entries = entries.filter((f) => f.name.endsWith('_enabled') && !['websocket_enabled', 'multi_tenant_enabled', 'audit_log_enabled'].includes(f.name));
    } else if (category === 'enterprise') {
      entries = entries.filter((f) => ['websocket_enabled', 'multi_tenant_enabled', 'audit_log_enabled'].includes(f.name));
    } else if (category === 'overridden') {
      entries = entries.filter((f) => f.override !== null);
    }

    return entries.sort((a, b) => a.name.localeCompare(b.name));
  }, [data, search, category]);

  const stats = useMemo(() => {
    if (!data?.flags) return { total: 0, enabled: 0, disabled: 0, overridden: 0 };
    const all = Object.values(data.flags);
    return {
      total: all.length,
      enabled: all.filter((f) => isEffectivelyEnabled(f)).length,
      disabled: all.filter((f) => !isEffectivelyEnabled(f)).length,
      overridden: all.filter((f) => f.override !== null).length,
    };
  }, [data]);

  const handleToggle = async (flag: FeatureFlag) => {
    const newValue = isEffectivelyEnabled(flag) ? 'false' : 'true';
    try {
      await setFlagMutation.mutateAsync({ name: flag.name, data: { value: newValue } });
      setSnackbar({ open: true, message: `${flag.name} set to ${newValue}`, severity: 'success' });
    } catch {
      setSnackbar({ open: true, message: `Failed to update ${flag.name}`, severity: 'error' });
    }
  };

  const handleKill = async (moduleName: string) => {
    try {
      await killMutation.mutateAsync(moduleName);
      setSnackbar({ open: true, message: `Module "${moduleName}" killed`, severity: 'success' });
    } catch {
      setSnackbar({ open: true, message: `Failed to kill "${moduleName}"`, severity: 'error' });
    }
  };

  const handleRestore = async (moduleName: string) => {
    try {
      await restoreMutation.mutateAsync(moduleName);
      setSnackbar({ open: true, message: `Module "${moduleName}" restored`, severity: 'success' });
    } catch {
      setSnackbar({ open: true, message: `Failed to restore "${moduleName}"`, severity: 'error' });
    }
  };

  const handleDelete = async (flagName: string) => {
    try {
      await deleteFlagMutation.mutateAsync(flagName);
      setSnackbar({ open: true, message: `Override for "${flagName}" removed`, severity: 'success' });
    } catch {
      setSnackbar({ open: true, message: `Failed to delete "${flagName}"`, severity: 'error' });
    }
  };

  const openEditDialog = (flag: FeatureFlag) => {
    setEditDialog({ open: true, flag });
    const type = getFlagType(flag);
    if (type === 'percentage') {
      setEditMode('percentage');
      setPercentValue(parseInt(flag.override?.replace('%', '') || '50', 10));
    } else if (type === 'whitelist') {
      setEditMode('whitelist');
      setWhitelistValue(flag.override?.replace('users:', '') || '');
    } else {
      setEditMode('boolean');
      setEditValue(isEffectivelyEnabled(flag) ? 'true' : 'false');
    }
  };

  const handleEditSave = async () => {
    if (!editDialog.flag) return;
    let value: string;
    if (editMode === 'boolean') {
      value = editValue;
    } else if (editMode === 'percentage') {
      value = `${percentValue}%`;
    } else {
      value = `users:${whitelistValue}`;
    }
    try {
      await setFlagMutation.mutateAsync({ name: editDialog.flag.name, data: { value } });
      setSnackbar({ open: true, message: `${editDialog.flag.name} updated`, severity: 'success' });
      setEditDialog({ open: false, flag: null });
    } catch {
      setSnackbar({ open: true, message: 'Failed to update flag', severity: 'error' });
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center mt-20">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-5">
        <Alert variant="destructive">
          <AlertDescription>Failed to load feature flags: {error.message}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="p-5 space-y-5 animate-enter">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
            <Flag className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">Feature Flags</h1>
            <p className="text-xs text-[var(--text-mid)]">Kill switches and percentage rollouts</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Total Flags', value: stats.total, color: 'text-[var(--accent)]' },
            { label: 'Enabled', value: stats.enabled, color: 'text-green-400' },
            { label: 'Disabled', value: stats.disabled, color: 'text-red-400' },
            { label: 'Overridden', value: stats.overridden, color: 'text-amber-400' },
          ].map((stat) => (
            <div key={stat.label} className="surface-card p-5 text-center">
              <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
              <p className="text-xs text-[var(--text-mid)]">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="surface-card p-5">
          <div className="flex gap-4 items-center flex-wrap">
            <div className="relative min-w-[250px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-low)]" />
              <Input
                placeholder="Search flags..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={category} onValueChange={(v) => setCategory(v as FlagCategory)}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Flags</SelectItem>
                <SelectItem value="modules">Modules</SelectItem>
                <SelectItem value="enterprise">Enterprise</SelectItem>
                <SelectItem value="overridden">Overridden</SelectItem>
              </SelectContent>
            </Select>
            <span className="text-sm text-[var(--text-mid)] ml-auto">
              {flags.length} flag{flags.length !== 1 ? 's' : ''} shown
            </span>
          </div>
        </div>

        {/* Flags Table */}
        <div className="surface-card p-5">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  <th className="text-left py-3 px-4 font-medium text-[var(--text-mid)]">Flag Name</th>
                  <th className="text-center py-3 px-4 font-medium text-[var(--text-mid)]">Status</th>
                  <th className="text-center py-3 px-4 font-medium text-[var(--text-mid)]">Type</th>
                  <th className="text-center py-3 px-4 font-medium text-[var(--text-mid)]">Override</th>
                  <th className="text-center py-3 px-4 font-medium text-[var(--text-mid)]">Default</th>
                  <th className="text-right py-3 px-4 font-medium text-[var(--text-mid)]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {flags.map((flag) => {
                  const enabled = isEffectivelyEnabled(flag);
                  const moduleName = getModuleName(flag.name);
                  const type = getFlagType(flag);

                  return (
                    <tr key={flag.name} className="border-b border-[var(--border)] hover:bg-[var(--bg-elevated)] transition-colors">
                      <td className="py-3 px-4">
                        <span className="font-mono text-sm text-[var(--text-high)]">
                          {flag.name}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Switch
                          checked={enabled}
                          onCheckedChange={() => handleToggle(flag)}
                        />
                      </td>
                      <td className="py-3 px-4 text-center">
                        {type === 'percentage' && (
                          <Badge variant="outline" className="gap-1">
                            <Percent className="h-3 w-3" /> {flag.override}
                          </Badge>
                        )}
                        {type === 'whitelist' && (
                          <Badge variant="secondary" className="gap-1">
                            <Users className="h-3 w-3" /> Whitelist
                          </Badge>
                        )}
                        {type === 'boolean' && (
                          <Badge variant="outline" className="gap-1">
                            <ToggleLeft className="h-3 w-3" /> Boolean
                          </Badge>
                        )}
                        {type === 'default' && (
                          <Badge variant="outline">Default</Badge>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {flag.override !== null ? (
                          <Badge variant="warning">{flag.override}</Badge>
                        ) : (
                          <span className="text-xs text-[var(--text-mid)]">--</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="text-xs text-[var(--text-mid)]">
                          {flag.default === null ? '--' : flag.default ? 'true' : 'false'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex justify-end gap-1">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEditDialog(flag)}>
                                <Flag className="h-3.5 w-3.5" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Advanced edit</TooltipContent>
                          </Tooltip>
                          {moduleName && enabled && (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-7 w-7 text-red-400 hover:text-red-300" onClick={() => handleKill(moduleName)}>
                                  <PowerOff className="h-3.5 w-3.5" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Kill {moduleName}</TooltipContent>
                            </Tooltip>
                          )}
                          {moduleName && !enabled && (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-7 w-7 text-green-400 hover:text-green-300" onClick={() => handleRestore(moduleName)}>
                                  <RotateCcw className="h-3.5 w-3.5" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Restore {moduleName}</TooltipContent>
                            </Tooltip>
                          )}
                          {flag.override !== null && (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleDelete(flag.name)}>
                                  <Trash2 className="h-3.5 w-3.5" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Reset to default</TooltipContent>
                            </Tooltip>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Edit Dialog */}
        <Dialog
          open={editDialog.open}
          onOpenChange={(v) => { if (!v) setEditDialog({ open: false, flag: null }); }}
        >
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Edit Flag: {editDialog.flag?.name}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-[var(--text-high)] mb-1 block">Mode</label>
                <Select value={editMode} onValueChange={(v) => setEditMode(v as 'boolean' | 'percentage' | 'whitelist')}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="boolean">Boolean (on/off)</SelectItem>
                    <SelectItem value="percentage">Percentage Rollout</SelectItem>
                    <SelectItem value="whitelist">User Whitelist</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              {editMode === 'boolean' && (
                <div>
                  <label className="text-sm font-medium text-[var(--text-high)] mb-1 block">Value</label>
                  <Select value={editValue} onValueChange={setEditValue}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="true">Enabled (true)</SelectItem>
                      <SelectItem value="false">Disabled (false)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}

              {editMode === 'percentage' && (
                <div>
                  <p className="text-sm text-[var(--text-high)] mb-4">
                    Rollout: {percentValue}% of users
                  </p>
                  <Slider
                    value={[percentValue]}
                    onValueChange={(v) => setPercentValue(v[0] ?? 0)}
                    min={0}
                    max={100}
                    step={1}
                  />
                  <div className="flex justify-between text-xs text-[var(--text-mid)] mt-1">
                    <span>0%</span>
                    <span>25%</span>
                    <span>50%</span>
                    <span>75%</span>
                    <span>100%</span>
                  </div>
                  <p className="text-xs text-[var(--text-mid)] mt-3">
                    Users are assigned deterministically based on their user ID hash.
                    The same users always get the same result for a given flag.
                  </p>
                </div>
              )}

              {editMode === 'whitelist' && (
                <div>
                  <label className="text-sm font-medium text-[var(--text-high)] mb-1 block">User IDs (comma-separated)</label>
                  <Textarea
                    rows={3}
                    value={whitelistValue}
                    onChange={(e) => setWhitelistValue(e.target.value)}
                    placeholder="550e8400-e29b-41d4-a716-446655440000, 6ba7b810-9dad-11d1-80b4-00c04fd430c8"
                  />
                  <p className="text-xs text-[var(--text-mid)] mt-1">
                    Enter user UUIDs separated by commas. Only these users will see the feature enabled.
                  </p>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="ghost" onClick={() => setEditDialog({ open: false, flag: null })}>Cancel</Button>
              <Button onClick={handleEditSave} disabled={setFlagMutation.isPending}>
                {setFlagMutation.isPending ? 'Saving...' : 'Save'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Snackbar / Toast */}
        {snackbar.open && (
          <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-in fade-in-0 slide-in-from-bottom-4">
            <Alert
              variant={snackbar.severity === 'error' ? 'destructive' : 'success'}
              className="flex items-center gap-2 pr-10 shadow-lg"
            >
              <AlertDescription>{snackbar.message}</AlertDescription>
              <button
                type="button"
                title="Dismiss"
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-white/10"
                onClick={() => setSnackbar((s) => ({ ...s, open: false }))}
              >
                &times;
              </button>
            </Alert>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
