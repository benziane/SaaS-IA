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
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  List,
  ListItem,
  ListItemText,
  Skeleton,
  TextField,
  Typography,
} from '@mui/material';

import {
  useCreateWorkspace,
  useDeleteWorkspace,
  useInviteMember,
  useMembers,
  useWorkspaces,
} from '@/features/workspaces/hooks/useWorkspaces';

const ROLE_COLORS: Record<string, 'primary' | 'success' | 'default'> = {
  owner: 'primary',
  editor: 'success',
  viewer: 'default',
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
      <Box sx={{ p: 3 }}>
        <Skeleton variant="text" width={200} height={40} sx={{ mb: 2 }} />
        <Grid container spacing={3}>
          {[1, 2].map((i) => (
            <Grid item xs={12} md={6} key={i}><Skeleton variant="rectangular" height={150} /></Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Workspaces</Typography>
        <Button variant="contained" onClick={() => setCreateOpen(true)}>Create Workspace</Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>Failed to load workspaces.</Alert>}
      {inviteMutation.isError && <Alert severity="error" sx={{ mb: 2 }}>{inviteMutation.error?.message}</Alert>}

      <Grid container spacing={3}>
        {/* Workspace Cards */}
        <Grid item xs={12} md={selectedWs ? 7 : 12}>
          {!workspaces?.length ? (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>No workspaces yet</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Create a workspace to collaborate with your team.
                </Typography>
                <Button variant="outlined" onClick={() => setCreateOpen(true)}>Create Workspace</Button>
              </CardContent>
            </Card>
          ) : (
            <Grid container spacing={2}>
              {workspaces.map((ws) => (
                <Grid item xs={12} sm={6} key={ws.id}>
                  <Card
                    variant={selectedWs === ws.id ? 'elevation' : 'outlined'}
                    sx={{
                      cursor: 'pointer',
                      border: selectedWs === ws.id ? '2px solid' : undefined,
                      borderColor: selectedWs === ws.id ? 'primary.main' : undefined,
                    }}
                    onClick={() => setSelectedWs(ws.id === selectedWs ? null : ws.id)}
                  >
                    <CardContent>
                      <Typography variant="h6">{ws.name}</Typography>
                      {ws.description && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{ws.description}</Typography>
                      )}
                      <Chip label={`${ws.member_count} members`} size="small" variant="outlined" />
                    </CardContent>
                    <CardActions>
                      <Button size="small" onClick={(e) => { e.stopPropagation(); setInviteOpen(ws.id); }}>
                        Invite
                      </Button>
                      <Button size="small" color="error" onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(ws.id); }}>
                        Delete
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Grid>

        {/* Members Panel */}
        {selectedWs && (
          <Grid item xs={12} md={5}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>Members</Typography>
                {members ? (
                  <List dense>
                    {members.map((m) => (
                      <ListItem key={m.id}>
                        <ListItemText primary={m.user_email} secondary={`Joined ${new Date(m.joined_at).toLocaleDateString()}`} />
                        <Chip label={m.role} size="small" color={ROLE_COLORS[m.role] || 'default'} />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Skeleton variant="rectangular" height={100} />
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Create Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Workspace</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Name" value={newName} onChange={(e) => setNewName(e.target.value)} sx={{ mt: 1, mb: 2 }} />
          <TextField fullWidth label="Description (optional)" value={newDesc} onChange={(e) => setNewDesc(e.target.value)} multiline rows={2} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={!newName.trim()}>Create</Button>
        </DialogActions>
      </Dialog>

      {/* Invite Dialog */}
      <Dialog open={!!inviteOpen} onClose={() => setInviteOpen(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Invite Member</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Email" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} sx={{ mt: 1, mb: 2 }} />
          <TextField
            fullWidth select label="Role" value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}
            SelectProps={{ native: true }}
          >
            <option value="viewer">Viewer</option>
            <option value="editor">Editor</option>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteOpen(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleInvite} disabled={!inviteEmail.trim()}>Invite</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
