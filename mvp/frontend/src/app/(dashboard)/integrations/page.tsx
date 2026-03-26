'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Skeleton,
  Tab,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import LinkIcon from '@mui/icons-material/Link';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import WebhookIcon from '@mui/icons-material/Webhook';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HubIcon from '@mui/icons-material/Hub';
import SettingsInputComponentIcon from '@mui/icons-material/SettingsInputComponent';

import {
  useConnectors,
  useCreateConnector,
  useCreateTrigger,
  useDeleteConnector,
  useDeleteTrigger,
  useEvents,
  useProviders,
  useTestConnector,
  useTriggers,
} from '@/features/integration-hub/hooks/useIntegrationHub';
import type { IntegrationConnector, ProviderInfo } from '@/features/integration-hub/types';

const STATUS_COLORS: Record<string, 'success' | 'error' | 'default' | 'warning'> = {
  active: 'success',
  error: 'error',
  disabled: 'default',
};

const EVENT_STATUS_COLORS: Record<string, 'info' | 'success' | 'error' | 'default'> = {
  received: 'info',
  processed: 'success',
  failed: 'error',
};

const PROVIDER_ICONS: Record<string, string> = {
  slack: '#4A154B',
  github: '#24292e',
  stripe: '#635bff',
  sendgrid: '#1A82e2',
  twilio: '#f22f46',
  notion: '#000000',
  linear: '#5E6AD2',
  google_drive: '#0F9D58',
  dropbox: '#0061FF',
  hubspot: '#ff7a59',
  custom: '#757575',
};

const ACTION_MODULES = [
  'transcription',
  'knowledge',
  'content_studio',
  'sentiment',
  'ai_workflows',
  'web_crawler',
  'agents',
  'data_analyst',
];

export default function IntegrationsPage() {
  const { data: providers, isLoading: providersLoading } = useProviders();
  const { data: connectors, isLoading: connectorsLoading } = useConnectors();
  const { data: triggers } = useTriggers();
  const createConnectorMutation = useCreateConnector();
  const deleteConnectorMutation = useDeleteConnector();
  const testConnectorMutation = useTestConnector();
  const createTriggerMutation = useCreateTrigger();
  const deleteTriggerMutation = useDeleteTrigger();

  const [tab, setTab] = useState(0);
  const [createOpen, setCreateOpen] = useState(false);
  const [triggerOpen, setTriggerOpen] = useState(false);
  const [selectedConnector, setSelectedConnector] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<Record<string, unknown> | null>(null);

  // Create connector form
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('webhook');
  const [newProvider, setNewProvider] = useState('');

  // Create trigger form
  const [triggerConnectorId, setTriggerConnectorId] = useState('');
  const [triggerEventType, setTriggerEventType] = useState('');
  const [triggerActionModule, setTriggerActionModule] = useState('');

  const { data: events } = useEvents(selectedConnector);

  const selectedProviderInfo = providers?.find((p: ProviderInfo) => p.slug === newProvider);

  const handleCreateConnector = () => {
    if (!newName.trim() || !newProvider) return;
    createConnectorMutation.mutate(
      { name: newName, type: newType, provider: newProvider, config: {}, enabled: true },
      {
        onSuccess: () => {
          setCreateOpen(false);
          setNewName('');
          setNewType('webhook');
          setNewProvider('');
        },
      }
    );
  };

  const handleTest = (connectorId: string) => {
    testConnectorMutation.mutate(connectorId, {
      onSuccess: (result) => setTestResult(result as unknown as Record<string, unknown>),
    });
  };

  const handleCreateTrigger = () => {
    if (!triggerConnectorId || !triggerEventType || !triggerActionModule) return;
    createTriggerMutation.mutate(
      {
        connector_id: triggerConnectorId,
        event_type: triggerEventType,
        action_module: triggerActionModule,
        action_config: {},
      },
      {
        onSuccess: () => {
          setTriggerOpen(false);
          setTriggerConnectorId('');
          setTriggerEventType('');
          setTriggerActionModule('');
        },
      }
    );
  };

  const copyWebhookUrl = (url: string) => {
    navigator.clipboard.writeText(url);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HubIcon color="primary" /> Integration Hub
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Connect external services via webhooks, OAuth2, and API keys
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<SettingsInputComponentIcon />}
            onClick={() => setTriggerOpen(true)}
            disabled={!connectors?.length}
          >
            New Trigger
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
            New Connector
          </Button>
        </Box>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label={`Providers (${providers?.length || 0})`} />
        <Tab label={`Connected (${connectors?.filter((c: IntegrationConnector) => c.is_active).length || 0})`} />
        <Tab label="Events Log" />
        <Tab label={`Triggers (${triggers?.length || 0})`} />
      </Tabs>

      {/* Tab 0: Available Providers */}
      {tab === 0 && (
        <>
          {providersLoading ? (
            <Grid container spacing={2}>
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <Grid item xs={12} sm={6} md={4} key={i}>
                  <Skeleton variant="rectangular" height={160} sx={{ borderRadius: 1 }} />
                </Grid>
              ))}
            </Grid>
          ) : (
            <Grid container spacing={2}>
              {providers?.map((provider: ProviderInfo) => {
                const connected = connectors?.find(
                  (c: IntegrationConnector) => c.provider === provider.slug && c.is_active
                );
                return (
                  <Grid item xs={12} sm={6} md={4} key={provider.slug}>
                    <Card
                      variant="outlined"
                      sx={{
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        borderLeft: 4,
                        borderLeftColor: PROVIDER_ICONS[provider.slug] || '#757575',
                      }}
                    >
                      <CardContent sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="subtitle1" fontWeight="bold">
                            {provider.name}
                          </Typography>
                          {connected && (
                            <Chip label="Connected" size="small" color="success" variant="outlined" />
                          )}
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                          {provider.description}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {provider.supported_types.map((t: string) => (
                            <Chip key={t} label={t} size="small" variant="outlined" />
                          ))}
                        </Box>
                      </CardContent>
                      <CardActions sx={{ px: 2, pb: 2 }}>
                        <Button
                          size="small"
                          variant={connected ? 'outlined' : 'contained'}
                          startIcon={connected ? <CheckCircleIcon /> : <LinkIcon />}
                          onClick={() => {
                            if (!connected) {
                              setNewProvider(provider.slug);
                              setNewName(`${provider.name} Integration`);
                              setNewType(provider.supported_types[0] || 'webhook');
                              setCreateOpen(true);
                            }
                          }}
                          disabled={!!connected}
                        >
                          {connected ? 'Connected' : 'Connect'}
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          )}
        </>
      )}

      {/* Tab 1: Connected Integrations */}
      {tab === 1 && (
        <>
          {connectorsLoading ? (
            <Grid container spacing={3}>
              {[1, 2, 3].map((i) => (
                <Grid item xs={12} sm={6} md={4} key={i}>
                  <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 1 }} />
                </Grid>
              ))}
            </Grid>
          ) : !connectors?.filter((c: IntegrationConnector) => c.is_active).length ? (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <HubIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">No integrations connected</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
                  Connect an external service to start receiving events
                </Typography>
                <Button variant="contained" onClick={() => setTab(0)}>Browse Providers</Button>
              </CardContent>
            </Card>
          ) : (
            <Grid container spacing={3}>
              {connectors
                ?.filter((c: IntegrationConnector) => c.is_active)
                .map((connector: IntegrationConnector) => (
                  <Grid item xs={12} sm={6} md={4} key={connector.id}>
                    <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                      <CardContent sx={{ flex: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="subtitle1" fontWeight="bold" noWrap>
                            {connector.name}
                          </Typography>
                          <Chip
                            label={connector.status}
                            size="small"
                            color={STATUS_COLORS[connector.status] || 'default'}
                          />
                        </Box>
                        <Box sx={{ display: 'flex', gap: 0.5, mb: 1.5 }}>
                          <Chip label={connector.provider} size="small" variant="outlined" />
                          <Chip label={connector.type} size="small" variant="outlined" />
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {connector.events_received} events received
                        </Typography>
                        {connector.last_event_at && (
                          <Typography variant="caption" color="text.secondary">
                            Last event: {new Date(connector.last_event_at).toLocaleString()}
                          </Typography>
                        )}
                        {connector.webhook_url && (
                          <Box sx={{ mt: 1.5 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                              Webhook URL:
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <Typography
                                variant="caption"
                                sx={{
                                  fontFamily: 'monospace',
                                  bgcolor: 'action.hover',
                                  px: 1,
                                  py: 0.5,
                                  borderRadius: 0.5,
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                  flex: 1,
                                }}
                              >
                                {connector.webhook_url}
                              </Typography>
                              <Tooltip title="Copy URL">
                                <IconButton size="small" onClick={() => copyWebhookUrl(connector.webhook_url!)}>
                                  <ContentCopyIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </Box>
                        )}
                      </CardContent>
                      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                        <Box>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => deleteConnectorMutation.mutate(connector.id)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => setSelectedConnector(
                              selectedConnector === connector.id ? null : connector.id
                            )}
                          >
                            <WebhookIcon fontSize="small" />
                          </IconButton>
                        </Box>
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={
                            testConnectorMutation.isPending
                              ? <CircularProgress size={14} color="inherit" />
                              : <PlayArrowIcon />
                          }
                          onClick={() => handleTest(connector.id)}
                          disabled={testConnectorMutation.isPending}
                        >
                          Test
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
            </Grid>
          )}
        </>
      )}

      {/* Tab 2: Events Log */}
      {tab === 2 && (
        <Box>
          {!selectedConnector ? (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <WebhookIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography color="text.secondary">
                  Select a connector from the Connected tab to view its events
                </Typography>
                {connectors && connectors.filter((c: IntegrationConnector) => c.is_active).length > 0 && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
                    {connectors
                      .filter((c: IntegrationConnector) => c.is_active)
                      .map((c: IntegrationConnector) => (
                        <Chip
                          key={c.id}
                          label={c.name}
                          clickable
                          onClick={() => setSelectedConnector(c.id)}
                          variant="outlined"
                        />
                      ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          ) : (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Typography variant="h6">
                  Events for: {connectors?.find((c: IntegrationConnector) => c.id === selectedConnector)?.name}
                </Typography>
                <Chip
                  label="Clear"
                  size="small"
                  variant="outlined"
                  onDelete={() => setSelectedConnector(null)}
                />
              </Box>
              {!events?.length ? (
                <Card>
                  <CardContent sx={{ textAlign: 'center', py: 4 }}>
                    <Typography color="text.secondary">No events received yet</Typography>
                  </CardContent>
                </Card>
              ) : (
                events.map((event) => (
                  <Card key={event.id} variant="outlined" sx={{ mb: 1 }}>
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip
                            label={event.status}
                            size="small"
                            color={EVENT_STATUS_COLORS[event.status] || 'default'}
                          />
                          <Chip label={event.event_type} size="small" variant="outlined" />
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(event.created_at).toLocaleString()}
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          mt: 1,
                          p: 1,
                          bgcolor: 'action.hover',
                          borderRadius: 1,
                          fontSize: '0.8rem',
                          fontFamily: 'monospace',
                          maxHeight: 100,
                          overflow: 'auto',
                        }}
                      >
                        {JSON.stringify(event.payload, null, 2).substring(0, 500)}
                      </Box>
                    </CardContent>
                  </Card>
                ))
              )}
            </Box>
          )}
        </Box>
      )}

      {/* Tab 3: Triggers */}
      {tab === 3 && (
        <Box>
          {!triggers?.length ? (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <SettingsInputComponentIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography variant="h6" color="text.secondary">No triggers configured</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
                  Create a trigger to automatically run actions when events are received
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setTriggerOpen(true)}
                  disabled={!connectors?.length}
                >
                  New Trigger
                </Button>
              </CardContent>
            </Card>
          ) : (
            triggers.map((trigger) => {
              const connector = connectors?.find(
                (c: IntegrationConnector) => c.id === trigger.connector_id
              );
              return (
                <Card key={trigger.id} variant="outlined" sx={{ mb: 1 }}>
                  <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle2">
                          {connector?.name || 'Unknown'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          on <strong>{trigger.event_type}</strong> {'->'} <strong>{trigger.action_module}</strong>
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={`${trigger.executions} runs`}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={trigger.is_active ? 'Active' : 'Inactive'}
                          size="small"
                          color={trigger.is_active ? 'success' : 'default'}
                        />
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => deleteTriggerMutation.mutate(trigger.id)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              );
            })
          )}
        </Box>
      )}

      {/* Events panel for selected connector (inline on Connected tab) */}
      {tab === 1 && selectedConnector && events && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Recent Events
            </Typography>
            {events.length === 0 ? (
              <Typography color="text.secondary">No events received yet</Typography>
            ) : (
              events.slice(0, 10).map((event) => (
                <Card key={event.id} variant="outlined" sx={{ mb: 1 }}>
                  <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={event.status}
                          size="small"
                          color={EVENT_STATUS_COLORS[event.status] || 'default'}
                        />
                        <Chip label={event.event_type} size="small" variant="outlined" />
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(event.created_at).toLocaleString()}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {/* Test Result Dialog */}
      <Dialog open={!!testResult} onClose={() => setTestResult(null)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {testResult?.success ? (
              <CheckCircleIcon color="success" />
            ) : (
              <ErrorIcon color="error" />
            )}
            Connection Test
          </Box>
        </DialogTitle>
        <DialogContent>
          {testResult && (
            <Box>
              <Alert severity={testResult.success ? 'success' : 'error'} sx={{ mb: 2 }}>
                {testResult.message as string}
              </Alert>
              <Typography variant="body2">
                Provider: <strong>{testResult.provider as string}</strong>
              </Typography>
              <Typography variant="body2">
                Type: <strong>{testResult.type as string}</strong>
              </Typography>
              {Boolean(testResult.webhook_url) && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2">Webhook URL:</Typography>
                  <Typography
                    variant="caption"
                    sx={{ fontFamily: 'monospace', bgcolor: 'action.hover', p: 1, borderRadius: 0.5, display: 'block', mt: 0.5 }}
                  >
                    {testResult.webhook_url as string}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestResult(null)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Create Connector Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Integration Connector</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Connector Name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            sx={{ mt: 1, mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Provider</InputLabel>
            <Select
              value={newProvider}
              label="Provider"
              onChange={(e) => {
                setNewProvider(e.target.value);
                const prov = providers?.find((p: ProviderInfo) => p.slug === e.target.value);
                if (prov) {
                  setNewType(prov.supported_types[0] || 'webhook');
                  if (!newName) setNewName(`${prov.name} Integration`);
                }
              }}
            >
              {providers?.map((p: ProviderInfo) => (
                <MenuItem key={p.slug} value={p.slug}>{p.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Type</InputLabel>
            <Select value={newType} label="Type" onChange={(e) => setNewType(e.target.value)}>
              {(selectedProviderInfo?.supported_types || ['webhook', 'oauth2', 'api_key']).map(
                (t: string) => (
                  <MenuItem key={t} value={t}>{t}</MenuItem>
                )
              )}
            </Select>
          </FormControl>
          {selectedProviderInfo && (
            <Box sx={{ p: 1.5, bgcolor: 'action.hover', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Supported events: {selectedProviderInfo.events.join(', ')}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateConnector}
            disabled={!newName.trim() || !newProvider || createConnectorMutation.isPending}
          >
            {createConnectorMutation.isPending ? <CircularProgress size={20} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Trigger Dialog */}
      <Dialog open={triggerOpen} onClose={() => setTriggerOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Event Trigger</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            When an event occurs on a connector, automatically execute an action in a platform module.
          </Typography>
          <FormControl fullWidth sx={{ mt: 1, mb: 2 }}>
            <InputLabel>Connector</InputLabel>
            <Select
              value={triggerConnectorId}
              label="Connector"
              onChange={(e) => setTriggerConnectorId(e.target.value)}
            >
              {connectors
                ?.filter((c: IntegrationConnector) => c.is_active)
                .map((c: IntegrationConnector) => (
                  <MenuItem key={c.id} value={c.id}>{c.name} ({c.provider})</MenuItem>
                ))}
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Event Type"
            placeholder="e.g., push, payment_intent.succeeded, message"
            value={triggerEventType}
            onChange={(e) => setTriggerEventType(e.target.value)}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Action Module</InputLabel>
            <Select
              value={triggerActionModule}
              label="Action Module"
              onChange={(e) => setTriggerActionModule(e.target.value)}
            >
              {ACTION_MODULES.map((m) => (
                <MenuItem key={m} value={m}>{m.replace(/_/g, ' ')}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTriggerOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateTrigger}
            disabled={
              !triggerConnectorId ||
              !triggerEventType.trim() ||
              !triggerActionModule ||
              createTriggerMutation.isPending
            }
          >
            {createTriggerMutation.isPending ? <CircularProgress size={20} /> : 'Create Trigger'}
          </Button>
        </DialogActions>
      </Dialog>

      {createConnectorMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>{createConnectorMutation.error?.message}</Alert>
      )}
      {createTriggerMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>{createTriggerMutation.error?.message}</Alert>
      )}
    </Box>
  );
}
