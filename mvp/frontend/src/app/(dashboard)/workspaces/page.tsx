'use client';

import { useState } from 'react';

import { Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
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
  useCreateWorkspace,
  useDeleteWorkspace,
  useInviteMember,
  useMembers,
  useWorkspaces,
} from '@/features/workspaces/hooks/useWorkspaces';

const ROLE_COLORS: Record<string, 'default' | 'success' | 'secondary'> = {
  owner: 'default',
  editor: 'success',
  viewer: 'secondary',
};

export default function WorkspacesPage() {
  const { data: workspaces, isLoading, error } = useWorkspaces();
  const createMutation = useCreateWorkspace();
  const deleteMutation = useDeleteWorkspace();
  const inviteMutation = useInviteMember();

  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [inviteOpen, setInviteOpen] = useState<string | null>(null);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('viewer');
  const [selectedWs, setSelectedWs] = useState<string | null>(null);

  const { data: members } = useMembers(selectedWs || '');

  const handleCreate = () => {
    if (!newName.trim()) { return; }
    createMutation.mutate(
      { name: newName.trim(), description: newDesc.trim() || undefined },
      { onSuccess: () => { setCreateOpen(false); setNewName(''); setNewDesc(''); } }
    );
  };

  const handleInvite = () => {
    if (!inviteEmail.trim() || !inviteOpen) { return; }
    inviteMutation.mutate(
      { workspaceId: inviteOpen, email: inviteEmail.trim(), role: inviteRole },
      { onSuccess: () => { setInviteOpen(null); setInviteEmail(''); } }
    );
  };

  if (isLoading) {
    return (
      <div className="p-5 space-y-5 animate-enter">
        <Skeleton className="w-48 h-10" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <Skeleton key={i} className="h-[150px]" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-5 space-y-5 animate-enter">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
            <Users className="h-5 w-5 text-[var(--accent)]" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">Workspaces</h1>
            <p className="text-xs text-[var(--text-mid)]">Manage your teams and collaboration spaces</p>
          </div>
        </div>
        <Button onClick={() => setCreateOpen(true)}>Create Workspace</Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>Failed to load workspaces.</AlertDescription>
        </Alert>
      )}
      {inviteMutation.isError && (
        <Alert variant="destructive">
          <AlertDescription>{inviteMutation.error?.message}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
        {/* Workspace Cards */}
        <div className={selectedWs ? 'md:col-span-7' : 'md:col-span-12'}>
          {!workspaces?.length ? (
            <div className="surface-card p-5 text-center py-12">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] mx-auto mb-4">
                <Users className="h-6 w-6 text-white" />
              </div>
              <h2 className="text-lg font-semibold text-[var(--text-mid)] mb-2">No workspaces yet</h2>
              <p className="text-sm text-[var(--text-mid)] mb-4">
                Create a workspace to collaborate with your team.
              </p>
              <Button variant="outline" onClick={() => setCreateOpen(true)}>Create Workspace</Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {workspaces.map((ws) => (
                <div
                  key={ws.id}
                  className={`surface-card border-glow-accent cursor-pointer transition-all ${
                    selectedWs === ws.id
                      ? 'border-l-4 border-l-[var(--accent)]'
                      : 'border-l-4 border-l-transparent'
                  }`}
                  onClick={() => setSelectedWs(ws.id === selectedWs ? null : ws.id)}
                >
                  <div className="p-5">
                    <h3 className="text-base font-semibold text-[var(--text-high)]">{ws.name}</h3>
                    {ws.description && (
                      <p className="text-sm text-[var(--text-mid)] mt-1 mb-2">{ws.description}</p>
                    )}
                    <Badge variant="outline" className="text-xs">{ws.member_count} members</Badge>
                  </div>
                  <div className="px-5 pb-4 flex gap-2">
                    <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); setInviteOpen(ws.id); }}>
                      Invite
                    </Button>
                    <Button size="sm" variant="ghost" className="text-red-400 hover:text-red-300" onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(ws.id); }}>
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Members Panel */}
        {selectedWs && (
          <div className="md:col-span-5">
            <div className="surface-card p-5">
              <h3 className="text-base font-semibold text-[var(--text-high)] mb-4">Members</h3>
              {members ? (
                <div className="space-y-1">
                  {members.map((m) => (
                    <div key={m.id} className="flex items-center justify-between py-2 border-b border-[var(--border)] last:border-0">
                      <div>
                        <p className="text-sm font-medium text-[var(--text-high)]">{m.user_email}</p>
                        <p className="text-xs text-[var(--text-low)]">Joined {new Date(m.joined_at).toLocaleDateString()}</p>
                      </div>
                      <Badge variant={ROLE_COLORS[m.role] || 'secondary'}>{m.role}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <Skeleton className="h-[100px]" />
              )}
            </div>
          </div>
        )}
      </div>

      {/* Create Dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Workspace</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Name</label>
              <Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Workspace name" />
            </div>
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Description (optional)</label>
              <Textarea value={newDesc} onChange={(e) => setNewDesc(e.target.value)} rows={2} placeholder="Description" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={!newName.trim()}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Invite Dialog */}
      <Dialog open={!!inviteOpen} onOpenChange={(open) => { if (!open) setInviteOpen(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Invite Member</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Email</label>
              <Input value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} placeholder="user@example.com" />
            </div>
            <div>
              <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Role</label>
              <Select value={inviteRole} onValueChange={setInviteRole}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="viewer">Viewer</SelectItem>
                  <SelectItem value="editor">Editor</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setInviteOpen(null)}>Cancel</Button>
            <Button onClick={handleInvite} disabled={!inviteEmail.trim()}>Invite</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
