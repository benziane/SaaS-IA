'use client';

import { useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Select,
  Slider,
  Snackbar,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import FlagIcon from '@mui/icons-material/Flag';
import SearchIcon from '@mui/icons-material/Search';
import PowerOffIcon from '@mui/icons-material/PowerOff';
import RestoreIcon from '@mui/icons-material/Restore';
import DeleteIcon from '@mui/icons-material/Delete';
import PeopleIcon from '@mui/icons-material/People';
import PercentIcon from '@mui/icons-material/Percent';
import ToggleOnIcon from '@mui/icons-material/ToggleOn';

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
  // Percentage or whitelist - show as "partial"
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

  const flags = useMemo(() => {
    if (!data?.flags) return [];
    let entries = Object.values(data.flags);

    // Filter by search
    if (search) {
      const s = search.toLowerCase();
      entries = entries.filter((f) => f.name.toLowerCase().includes(s));
    }

    // Filter by category
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
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Failed to load feature flags: {error.message}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FlagIcon color="primary" /> Feature Flags
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Runtime feature control -- toggle modules, percentage rollouts, and user whitelists without redeployment
        </Typography>
      </Box>

      {/* Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {[
          { label: 'Total Flags', value: stats.total, color: 'primary.main' },
          { label: 'Enabled', value: stats.enabled, color: 'success.main' },
          { label: 'Disabled', value: stats.disabled, color: 'error.main' },
          { label: 'Overridden', value: stats.overridden, color: 'warning.main' },
        ].map((stat) => (
          <Grid item xs={6} sm={3} key={stat.label}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center', py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Typography variant="h4" sx={{ color: stat.color }}>{stat.value}</Typography>
                <Typography variant="caption" color="text.secondary">{stat.label}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <TextField
            size="small"
            placeholder="Search flags..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 250 }}
          />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={category}
              label="Category"
              onChange={(e) => setCategory(e.target.value as FlagCategory)}
            >
              <MenuItem value="all">All Flags</MenuItem>
              <MenuItem value="modules">Modules</MenuItem>
              <MenuItem value="enterprise">Enterprise</MenuItem>
              <MenuItem value="overridden">Overridden</MenuItem>
            </Select>
          </FormControl>
          <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
            {flags.length} flag{flags.length !== 1 ? 's' : ''} shown
          </Typography>
        </CardContent>
      </Card>

      {/* Flags Table */}
      <TableContainer component={Card}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Flag Name</TableCell>
              <TableCell align="center">Status</TableCell>
              <TableCell align="center">Type</TableCell>
              <TableCell align="center">Override</TableCell>
              <TableCell align="center">Default</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {flags.map((flag) => {
              const enabled = isEffectivelyEnabled(flag);
              const moduleName = getModuleName(flag.name);
              const type = getFlagType(flag);

              return (
                <TableRow key={flag.name} hover>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {flag.name}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Switch
                      checked={enabled}
                      onChange={() => handleToggle(flag)}
                      size="small"
                      color={enabled ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell align="center">
                    {type === 'percentage' && (
                      <Chip icon={<PercentIcon />} label={flag.override} size="small" color="info" variant="outlined" />
                    )}
                    {type === 'whitelist' && (
                      <Chip icon={<PeopleIcon />} label="Whitelist" size="small" color="secondary" variant="outlined" />
                    )}
                    {type === 'boolean' && (
                      <Chip icon={<ToggleOnIcon />} label="Boolean" size="small" variant="outlined" />
                    )}
                    {type === 'default' && (
                      <Chip label="Default" size="small" variant="outlined" color="default" />
                    )}
                  </TableCell>
                  <TableCell align="center">
                    {flag.override !== null ? (
                      <Chip label={flag.override} size="small" color="warning" variant="filled" />
                    ) : (
                      <Typography variant="caption" color="text.secondary">--</Typography>
                    )}
                  </TableCell>
                  <TableCell align="center">
                    <Typography variant="caption">
                      {flag.default === null ? '--' : flag.default ? 'true' : 'false'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 0.5 }}>
                      <Tooltip title="Advanced edit">
                        <IconButton size="small" onClick={() => openEditDialog(flag)}>
                          <FlagIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      {moduleName && enabled && (
                        <Tooltip title={`Kill ${moduleName}`}>
                          <IconButton size="small" color="error" onClick={() => handleKill(moduleName)}>
                            <PowerOffIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      {moduleName && !enabled && (
                        <Tooltip title={`Restore ${moduleName}`}>
                          <IconButton size="small" color="success" onClick={() => handleRestore(moduleName)}>
                            <RestoreIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      {flag.override !== null && (
                        <Tooltip title="Reset to default">
                          <IconButton size="small" onClick={() => handleDelete(flag.name)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Edit Dialog */}
      <Dialog
        open={editDialog.open}
        onClose={() => setEditDialog({ open: false, flag: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Edit Flag: {editDialog.flag?.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 1 }}>
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Mode</InputLabel>
              <Select
                value={editMode}
                label="Mode"
                onChange={(e) => setEditMode(e.target.value as 'boolean' | 'percentage' | 'whitelist')}
              >
                <MenuItem value="boolean">Boolean (on/off)</MenuItem>
                <MenuItem value="percentage">Percentage Rollout</MenuItem>
                <MenuItem value="whitelist">User Whitelist</MenuItem>
              </Select>
            </FormControl>

            <Divider sx={{ mb: 2 }} />

            {editMode === 'boolean' && (
              <FormControl fullWidth>
                <InputLabel>Value</InputLabel>
                <Select
                  value={editValue}
                  label="Value"
                  onChange={(e) => setEditValue(e.target.value)}
                >
                  <MenuItem value="true">Enabled (true)</MenuItem>
                  <MenuItem value="false">Disabled (false)</MenuItem>
                </Select>
              </FormControl>
            )}

            {editMode === 'percentage' && (
              <Box>
                <Typography gutterBottom>
                  Rollout: {percentValue}% of users
                </Typography>
                <Slider
                  value={percentValue}
                  onChange={(_, v) => setPercentValue(v as number)}
                  min={0}
                  max={100}
                  step={1}
                  marks={[
                    { value: 0, label: '0%' },
                    { value: 25, label: '25%' },
                    { value: 50, label: '50%' },
                    { value: 75, label: '75%' },
                    { value: 100, label: '100%' },
                  ]}
                  valueLabelDisplay="auto"
                />
                <Typography variant="caption" color="text.secondary">
                  Users are assigned deterministically based on their user ID hash.
                  The same users always get the same result for a given flag.
                </Typography>
              </Box>
            )}

            {editMode === 'whitelist' && (
              <TextField
                fullWidth
                multiline
                rows={3}
                label="User IDs (comma-separated)"
                value={whitelistValue}
                onChange={(e) => setWhitelistValue(e.target.value)}
                helperText="Enter user UUIDs separated by commas. Only these users will see the feature enabled."
                placeholder="550e8400-e29b-41d4-a716-446655440000, 6ba7b810-9dad-11d1-80b4-00c04fd430c8"
              />
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog({ open: false, flag: null })}>Cancel</Button>
          <Button variant="contained" onClick={handleEditSave} disabled={setFlagMutation.isPending}>
            {setFlagMutation.isPending ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
