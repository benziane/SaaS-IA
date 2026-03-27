'use client';

import { useState } from 'react';
import {
  Plus, Trash2, Link2, Play, Webhook, Copy, CheckCircle, XCircle,
  Network, Settings2, Loader2, Plug,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/lib/design-hub/components/Tabs';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/lib/design-hub/components/Dialog';

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

const STATUS_VARIANTS: Record<string, 'success' | 'destructive' | 'default' | 'warning'> = {
  active: 'success',
  error: 'destructive',
  disabled: 'default',
};

const EVENT_STATUS_VARIANTS: Record<string, 'secondary' | 'success' | 'destructive' | 'default'> = {
  received: 'secondary',
  processed: 'success',
  failed: 'destructive',
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
  'transcription', 'knowledge', 'content_studio', 'sentiment',
  'ai_workflows', 'web_crawler', 'agents', 'data_analyst',
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

  const [tab, setTab] = useState('providers');
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

  const activeConnectors = connectors?.filter((c: IntegrationConnector) => c.is_active) || [];

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
            <Plug className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">Integration Hub</h1>
            <p className="text-xs text-[var(--text-mid)]">Connect external services and webhooks</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setTriggerOpen(true)} disabled={!connectors?.length}>
            <Settings2 className="h-4 w-4 mr-2" /> New Trigger
          </Button>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-2" /> New Connector
          </Button>
        </div>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="mb-6">
          <TabsTrigger value="providers">Providers ({providers?.length || 0})</TabsTrigger>
          <TabsTrigger value="connected">Connected ({activeConnectors.length})</TabsTrigger>
          <TabsTrigger value="events">Events Log</TabsTrigger>
          <TabsTrigger value="triggers">Triggers ({triggers?.length || 0})</TabsTrigger>
        </TabsList>

        {/* Tab 0: Available Providers */}
        <TabsContent value="providers">
          {providersLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <Skeleton key={i} className="h-40 rounded-lg" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {providers?.map((provider: ProviderInfo) => {
                const connected = connectors?.find(
                  (c: IntegrationConnector) => c.provider === provider.slug && c.is_active
                );
                return (
                  <div
                    key={provider.slug}
                    className="surface-card p-5 flex flex-col h-full border-l-4"
                    style={{ borderLeftColor: PROVIDER_ICONS[provider.slug] || '#757575' }}
                  >
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-[var(--text-high)]">{provider.name}</span>
                        {connected && <Badge variant="outline" className="text-green-600 border-green-600">Connected</Badge>}
                      </div>
                      <p className="text-sm text-[var(--text-mid)] mb-3">{provider.description}</p>
                      <div className="flex gap-1 flex-wrap">
                        {provider.supported_types.map((t: string) => (
                          <Badge key={t} variant="outline">{t}</Badge>
                        ))}
                      </div>
                    </div>
                    <div className="mt-4">
                      <Button
                        size="sm"
                        variant={connected ? 'outline' : 'default'}
                        disabled={!!connected}
                        onClick={() => {
                          if (!connected) {
                            setNewProvider(provider.slug);
                            setNewName(`${provider.name} Integration`);
                            setNewType(provider.supported_types[0] || 'webhook');
                            setCreateOpen(true);
                          }
                        }}
                      >
                        {connected ? (
                          <><CheckCircle className="h-3.5 w-3.5 mr-1" /> Connected</>
                        ) : (
                          <><Link2 className="h-3.5 w-3.5 mr-1" /> Connect</>
                        )}
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Tab 1: Connected Integrations */}
        <TabsContent value="connected">
          {connectorsLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-52 rounded-lg" />
              ))}
            </div>
          ) : !activeConnectors.length ? (
            <div className="surface-card p-5">
              <div className="text-center py-16 px-6">
                <Network className="h-16 w-16 text-[var(--text-low)] mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-[var(--text-mid)]">No integrations connected</h3>
                <p className="text-sm text-[var(--text-mid)] mt-2 mb-4">
                  Connect an external service to start receiving events
                </p>
                <Button onClick={() => setTab('providers')}>Browse Providers</Button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              {activeConnectors.map((connector: IntegrationConnector) => (
                <div key={connector.id} className="surface-card p-5 flex flex-col h-full border border-[var(--border)]">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-[var(--text-high)] truncate">{connector.name}</span>
                      <Badge variant={STATUS_VARIANTS[connector.status] || 'default'}>{connector.status}</Badge>
                    </div>
                    <div className="flex gap-1 mb-3">
                      <Badge variant="outline">{connector.provider}</Badge>
                      <Badge variant="outline">{connector.type}</Badge>
                    </div>
                    <p className="text-sm text-[var(--text-mid)]">{connector.events_received} events received</p>
                    {connector.last_event_at && (
                      <span className="text-xs text-[var(--text-mid)]">
                        Last event: {new Date(connector.last_event_at).toLocaleString()}
                      </span>
                    )}
                    {connector.webhook_url && (
                      <div className="mt-3">
                        <span className="text-xs text-[var(--text-mid)] block mb-1">Webhook URL:</span>
                        <div className="flex items-center gap-1">
                          <span className="text-xs font-mono bg-[var(--bg-surface)] px-2 py-1 rounded truncate flex-1">
                            {connector.webhook_url}
                          </span>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button type="button" title="Copy URL" className="p-1 rounded hover:bg-[var(--bg-hover)]" onClick={() => copyWebhookUrl(connector.webhook_url!)}>
                                  <Copy className="h-3.5 w-3.5 text-[var(--text-mid)]" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent>Copy URL</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--border)]">
                    <div className="flex gap-1">
                      <button type="button" title="Delete" className="p-1.5 rounded hover:bg-red-100 text-red-500" onClick={() => deleteConnectorMutation.mutate(connector.id)}>
                        <Trash2 className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        title="View events"
                        className="p-1.5 rounded hover:bg-[var(--bg-hover)]"
                        onClick={() => setSelectedConnector(selectedConnector === connector.id ? null : connector.id)}
                      >
                        <Webhook className="h-4 w-4 text-[var(--text-mid)]" />
                      </button>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTest(connector.id)}
                      disabled={testConnectorMutation.isPending}
                    >
                      {testConnectorMutation.isPending ? (
                        <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
                      ) : (
                        <Play className="h-3.5 w-3.5 mr-1" />
                      )}
                      Test
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Events panel for selected connector */}
          {selectedConnector && events && (
            <div className="surface-card p-5 mt-5">
              <h3 className="text-lg font-semibold text-[var(--text-high)] mb-4">Recent Events</h3>
              {events.length === 0 ? (
                <p className="text-sm text-[var(--text-mid)]">No events received yet</p>
              ) : (
                events.slice(0, 10).map((event) => (
                  <div key={event.id} className="mb-2 border border-[var(--border)] rounded-lg py-2 px-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant={EVENT_STATUS_VARIANTS[event.status] || 'default'}>{event.status}</Badge>
                        <Badge variant="outline">{event.event_type}</Badge>
                      </div>
                      <span className="text-xs text-[var(--text-mid)]">
                        {new Date(event.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </TabsContent>

        {/* Tab 2: Events Log */}
        <TabsContent value="events">
          {!selectedConnector ? (
            <div className="surface-card p-5">
              <div className="text-center py-12 px-6">
                <Webhook className="h-12 w-12 text-[var(--text-low)] mx-auto mb-2" />
                <p className="text-[var(--text-mid)]">
                  Select a connector from the Connected tab to view its events
                </p>
                {activeConnectors.length > 0 && (
                  <div className="mt-4 flex gap-2 justify-center flex-wrap">
                    {activeConnectors.map((c: IntegrationConnector) => (
                      <Badge
                        key={c.id}
                        variant="outline"
                        className="cursor-pointer hover:bg-[var(--bg-hover)]"
                        onClick={() => setSelectedConnector(c.id)}
                      >
                        {c.name}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <h3 className="text-lg font-semibold text-[var(--text-high)]">
                  Events for: {connectors?.find((c: IntegrationConnector) => c.id === selectedConnector)?.name}
                </h3>
                <Badge variant="outline" className="cursor-pointer" onClick={() => setSelectedConnector(null)}>
                  Clear
                </Badge>
              </div>
              {!events?.length ? (
                <div className="surface-card p-5">
                  <div className="text-center py-8 px-6">
                    <p className="text-[var(--text-mid)]">No events received yet</p>
                  </div>
                </div>
              ) : (
                events.map((event) => (
                  <div key={event.id} className="surface-card p-5 mb-2 border border-[var(--border)]">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant={EVENT_STATUS_VARIANTS[event.status] || 'default'}>{event.status}</Badge>
                        <Badge variant="outline">{event.event_type}</Badge>
                      </div>
                      <span className="text-xs text-[var(--text-mid)]">
                        {new Date(event.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="mt-2 p-2 bg-[var(--bg-surface)] rounded text-xs font-mono max-h-24 overflow-auto">
                      {JSON.stringify(event.payload, null, 2).substring(0, 500)}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </TabsContent>

        {/* Tab 3: Triggers */}
        <TabsContent value="triggers">
          {!triggers?.length ? (
            <div className="surface-card p-5">
              <div className="text-center py-12 px-6">
                <Settings2 className="h-12 w-12 text-[var(--text-low)] mx-auto mb-2" />
                <h3 className="text-lg font-semibold text-[var(--text-mid)]">No triggers configured</h3>
                <p className="text-sm text-[var(--text-mid)] mt-2 mb-4">
                  Create a trigger to automatically run actions when events are received
                </p>
                <Button onClick={() => setTriggerOpen(true)} disabled={!connectors?.length}>
                  <Plus className="h-4 w-4 mr-2" /> New Trigger
                </Button>
              </div>
            </div>
          ) : (
            triggers.map((trigger) => {
              const connector = connectors?.find(
                (c: IntegrationConnector) => c.id === trigger.connector_id
              );
              return (
                <div key={trigger.id} className="surface-card p-5 mb-2 border border-[var(--border)]">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-[var(--text-high)]">
                        {connector?.name || 'Unknown'}
                      </span>
                      <span className="text-sm text-[var(--text-mid)]">
                        on <strong>{trigger.event_type}</strong> {'->'} <strong>{trigger.action_module}</strong>
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{trigger.executions} runs</Badge>
                      <Badge variant={trigger.is_active ? 'success' : 'default'}>
                        {trigger.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                      <button
                        type="button"
                        title="Delete"
                        className="p-1 rounded hover:bg-red-100 text-red-500"
                        onClick={() => deleteTriggerMutation.mutate(trigger.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </TabsContent>
      </Tabs>

      {/* Test Result Dialog */}
      <Dialog open={!!testResult} onOpenChange={(v) => { if (!v) setTestResult(null); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {testResult?.success ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500" />
              )}
              Connection Test
            </DialogTitle>
          </DialogHeader>
          {testResult && (
            <div className="space-y-3">
              <Alert variant={testResult.success ? 'default' : 'destructive'}>
                <AlertDescription>{testResult.message as string}</AlertDescription>
              </Alert>
              <p className="text-sm text-[var(--text-high)]">
                Provider: <strong>{testResult.provider as string}</strong>
              </p>
              <p className="text-sm text-[var(--text-high)]">
                Type: <strong>{testResult.type as string}</strong>
              </p>
              {Boolean(testResult.webhook_url) && (
                <div>
                  <p className="text-sm text-[var(--text-high)]">Webhook URL:</p>
                  <span className="text-xs font-mono bg-[var(--bg-surface)] p-2 rounded block mt-1">
                    {testResult.webhook_url as string}
                  </span>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setTestResult(null)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Connector Dialog */}
      <Dialog open={createOpen} onOpenChange={(v) => { if (!v) setCreateOpen(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>New Integration Connector</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <Input
              placeholder="Connector Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
            <div>
              <label className="text-xs text-[var(--text-mid)] mb-1 block">Provider</label>
              <Select
                value={newProvider}
                onValueChange={(val) => {
                  setNewProvider(val);
                  const prov = providers?.find((p: ProviderInfo) => p.slug === val);
                  if (prov) {
                    setNewType(prov.supported_types[0] || 'webhook');
                    if (!newName) setNewName(`${prov.name} Integration`);
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                  {providers?.map((p: ProviderInfo) => (
                    <SelectItem key={p.slug} value={p.slug}>{p.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-[var(--text-mid)] mb-1 block">Type</label>
              <Select value={newType} onValueChange={setNewType}>
                <SelectTrigger>
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  {(selectedProviderInfo?.supported_types || ['webhook', 'oauth2', 'api_key']).map(
                    (t: string) => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    )
                  )}
                </SelectContent>
              </Select>
            </div>
            {selectedProviderInfo && (
              <div className="p-3 bg-[var(--bg-surface)] rounded">
                <span className="text-xs text-[var(--text-mid)]">
                  Supported events: {selectedProviderInfo.events.join(', ')}
                </span>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCreateConnector}
              disabled={!newName.trim() || !newProvider || createConnectorMutation.isPending}
            >
              {createConnectorMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Trigger Dialog */}
      <Dialog open={triggerOpen} onOpenChange={(v) => { if (!v) setTriggerOpen(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>New Event Trigger</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-2">
            <p className="text-sm text-[var(--text-mid)]">
              When an event occurs on a connector, automatically execute an action in a platform module.
            </p>
            <div>
              <label className="text-xs text-[var(--text-mid)] mb-1 block">Connector</label>
              <Select value={triggerConnectorId} onValueChange={setTriggerConnectorId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select connector" />
                </SelectTrigger>
                <SelectContent>
                  {activeConnectors.map((c: IntegrationConnector) => (
                    <SelectItem key={c.id} value={c.id}>{c.name} ({c.provider})</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Input
              placeholder="Event Type (e.g., push, payment_intent.succeeded, message)"
              value={triggerEventType}
              onChange={(e) => setTriggerEventType(e.target.value)}
            />
            <div>
              <label className="text-xs text-[var(--text-mid)] mb-1 block">Action Module</label>
              <Select value={triggerActionModule} onValueChange={setTriggerActionModule}>
                <SelectTrigger>
                  <SelectValue placeholder="Select module" />
                </SelectTrigger>
                <SelectContent>
                  {ACTION_MODULES.map((m) => (
                    <SelectItem key={m} value={m}>{m.replace(/_/g, ' ')}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTriggerOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCreateTrigger}
              disabled={
                !triggerConnectorId ||
                !triggerEventType.trim() ||
                !triggerActionModule ||
                createTriggerMutation.isPending
              }
            >
              {createTriggerMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create Trigger'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {createConnectorMutation.isError && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{createConnectorMutation.error?.message}</AlertDescription>
        </Alert>
      )}
      {createTriggerMutation.isError && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{createTriggerMutation.error?.message}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
