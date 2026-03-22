/**
 * Workspace hooks
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  addComment,
  createWorkspace,
  deleteWorkspace,
  inviteMember,
  listComments,
  listMembers,
  listSharedItems,
  listWorkspaces,
  removeMember,
} from '../api';
import type { Workspace, WorkspaceComment, WorkspaceCreateRequest, WorkspaceMember, SharedItem } from '../types';

export function useWorkspaces() {
  return useQuery<Workspace[]>({
    queryKey: ['workspaces'],
    queryFn: listWorkspaces,
  });
}

export function useCreateWorkspace() {
  const qc = useQueryClient();
  return useMutation<Workspace, Error, WorkspaceCreateRequest>({
    mutationFn: createWorkspace,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['workspaces'] }); },
  });
}

export function useDeleteWorkspace() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteWorkspace,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['workspaces'] }); },
  });
}

export function useMembers(workspaceId: string) {
  return useQuery<WorkspaceMember[]>({
    queryKey: ['workspaces', workspaceId, 'members'],
    queryFn: () => listMembers(workspaceId),
    enabled: !!workspaceId,
  });
}

export function useInviteMember() {
  const qc = useQueryClient();
  return useMutation<WorkspaceMember, Error, { workspaceId: string; email: string; role: string }>({
    mutationFn: ({ workspaceId, email, role }) => inviteMember(workspaceId, email, role),
    onSuccess: (_, vars) => { qc.invalidateQueries({ queryKey: ['workspaces', vars.workspaceId, 'members'] }); },
  });
}

export function useRemoveMember() {
  const qc = useQueryClient();
  return useMutation<void, Error, { workspaceId: string; userId: string }>({
    mutationFn: ({ workspaceId, userId }) => removeMember(workspaceId, userId),
    onSuccess: (_, vars) => { qc.invalidateQueries({ queryKey: ['workspaces', vars.workspaceId, 'members'] }); },
  });
}

export function useSharedItems(workspaceId: string) {
  return useQuery<SharedItem[]>({
    queryKey: ['workspaces', workspaceId, 'items'],
    queryFn: () => listSharedItems(workspaceId),
    enabled: !!workspaceId,
  });
}

export function useComments(itemId: string) {
  return useQuery<WorkspaceComment[]>({
    queryKey: ['comments', itemId],
    queryFn: () => listComments(itemId),
    enabled: !!itemId,
  });
}

export function useAddComment() {
  const qc = useQueryClient();
  return useMutation<WorkspaceComment, Error, { itemId: string; content: string }>({
    mutationFn: ({ itemId, content }) => addComment(itemId, content),
    onSuccess: (_, vars) => { qc.invalidateQueries({ queryKey: ['comments', vars.itemId] }); },
  });
}
