'use client';

import { useState } from 'react';
import { Code2, Copy, X } from 'lucide-react';

import { Button } from '@/lib/design-hub/components/Button';
import { Badge } from '@/lib/design-hub/components/Badge';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Input } from '@/lib/design-hub/components/Input';
import { Separator } from '@/lib/design-hub/components/Separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
} from '@/lib/design-hub/components/Dialog';

import { useAPIKeys, useCreateAPIKey, useRevokeAPIKey } from '@/features/api-keys/hooks/useAPIKeys';
import type { APIKeyCreated } from '@/features/api-keys/types';

const API_EXAMPLES = [
  {
    title: 'Transcribe a video',
    method: 'POST',
    endpoint: '/v1/transcribe',
    curl: `curl -X POST http://localhost:8004/v1/transcribe \\
  -H "X-API-Key: YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"video_url": "https://youtube.com/watch?v=...", "language": "auto"}'`,
  },
  {
    title: 'Process text with AI',
    method: 'POST',
    endpoint: '/v1/process',
    curl: `curl -X POST http://localhost:8004/v1/process \\
  -H "X-API-Key: YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Your text here", "task": "summarize", "provider": "gemini"}'`,
  },
  {
    title: 'Check job status',
    method: 'GET',
    endpoint: '/v1/jobs/{job_id}',
    curl: `curl http://localhost:8004/v1/jobs/JOB_ID \\
  -H "X-API-Key: YOUR_KEY"`,
  },
];

export default function APIDocsPage() {
  const { data: keys, isLoading } = useAPIKeys();
  const createMutation = useCreateAPIKey();
  const revokeMutation = useRevokeAPIKey();
  const [createOpen, setCreateOpen] = useState(false);
  const [keyName, setKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState<APIKeyCreated | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCreate = () => {
    if (!keyName.trim()) return;
    createMutation.mutate(
      { name: keyName.trim() },
      {
        onSuccess: (data) => {
          setCreatedKey(data);
          setCreateOpen(false);
          setKeyName('');
        },
      }
    );
  };

  const handleCopy = () => {
    if (createdKey) {
      navigator.clipboard.writeText(createdKey.key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
          <Code2 className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-high)]">API Documentation &amp; Keys</h1>
          <p className="text-xs text-[var(--text-mid)]">Interactive API reference</p>
        </div>
      </div>

      {/* Created Key Alert */}
      {createdKey && (
        <Alert variant="warning" className="relative">
          <button
            type="button"
            onClick={() => setCreatedKey(null)}
            className="absolute right-3 top-3 text-[var(--text-low)] hover:text-[var(--text-high)]"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
          <AlertTitle>Your API key (save it now - it won&apos;t be shown again):</AlertTitle>
          <AlertDescription>
            <div className="flex items-center gap-2 mt-1">
              <code className="text-sm break-all">{createdKey.key}</code>
              <Button size="sm" variant="outline" onClick={handleCopy}>
                <Copy className="h-3 w-3 mr-1" />
                {copied ? 'Copied!' : 'Copy'}
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* API Keys Management */}
        <div className="md:col-span-5">
          <div className="surface-card p-5">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-[var(--text-high)]">API Keys</h2>
              <Button size="sm" onClick={() => setCreateOpen(true)}>
                Create Key
              </Button>
            </div>

            {isLoading ? (
              <Skeleton className="h-[150px] w-full" />
            ) : !keys?.length ? (
              <p className="text-sm text-[var(--text-mid)]">
                No API keys created yet.
              </p>
            ) : (
              <div className="space-y-1">
                {keys.map((key) => (
                  <div
                    key={key.id}
                    className="flex items-center justify-between py-2 px-1"
                  >
                    <div>
                      <p className="text-sm font-medium text-[var(--text-high)]">{key.name}</p>
                      <p className="text-xs text-[var(--text-mid)]">
                        {key.key_prefix}... |{' '}
                        {key.last_used_at
                          ? `Last used: ${new Date(key.last_used_at).toLocaleDateString()}`
                          : 'Never used'}
                      </p>
                    </div>
                    {key.is_active ? (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => revokeMutation.mutate(key.id)}
                      >
                        Revoke
                      </Button>
                    ) : (
                      <Badge variant="secondary">Revoked</Badge>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* API Documentation */}
        <div className="md:col-span-7">
          <div className="surface-card p-5">
            <h2 className="text-lg font-semibold text-[var(--text-high)] mb-4">
              Public API v1
            </h2>
            <p className="text-sm text-[var(--text-mid)] mb-6">
              Authenticate using the <code className="bg-[var(--bg-elevated)] px-1 rounded text-xs">X-API-Key</code> header with your API key.
            </p>

            {API_EXAMPLES.map((example, idx) => (
              <div key={idx} className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="default">{example.method}</Badge>
                  <span className="text-sm font-semibold text-[var(--text-high)]">{example.endpoint}</span>
                </div>
                <p className="text-sm text-[var(--text-mid)] mb-2">{example.title}</p>
                <div className="bg-gray-900 text-gray-100 p-4 rounded-md font-mono text-xs whitespace-pre-wrap overflow-auto">
                  {example.curl}
                </div>
                {idx < API_EXAMPLES.length - 1 && <Separator className="mt-4" />}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Create Key Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create API Key</DialogTitle>
          </DialogHeader>
          <div className="py-2">
            <label className="text-sm font-medium text-[var(--text-mid)] mb-1.5 block">
              Key Name
            </label>
            <Input
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              placeholder="e.g., Production, Testing"
            />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!keyName.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? 'Creating...' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
