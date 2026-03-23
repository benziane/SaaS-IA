/**
 * Workspace API
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type { SharedItem, Workspace, WorkspaceComment, WorkspaceCreateRequest, WorkspaceMember } from './types';

const WS_ENDPOINTS = {
  LIST: '/api/workspaces',
  CREATE: '/api/workspaces',
  GET: (id: string) => `/api/workspaces/${id}`,
  UPDATE: (id: string) => `/api/workspaces/${id}`,
  DELETE: (id: string) => `/api/workspaces/${id}`,
  INVITE: (id: string) => `/api/workspaces/${id}/invite`,
  MEMBERS: (id: string) => `/api/workspaces/${id}/members`,
  REMOVE_MEMBER: (wsId: string, userId: string) => `/api/workspaces/${wsId}/members/${userId}`,
  SHARE: (id: string) => `/api/workspaces/${id}/share`,
  ITEMS: (id: string) => `/api/workspaces/${id}/items`,
  COMMENTS: (itemId: string) => `/api/workspaces/items/${itemId}/comments`,
} as const;

export async function listWorkspaces(): Promise<Workspace[]> {
  const response: AxiosResponse<Workspace[]> = await apiClient.get(WS_ENDPOINTS.LIST);
  return response.data;
}

export async function createWorkspace(data: WorkspaceCreateRequest): Promise<Workspace> {
  const response: AxiosResponse<Workspace> = await apiClient.post(WS_ENDPOINTS.CREATE, data);
  return response.data;
}

export async function getWorkspace(id: string): Promise<Workspace> {
  const response: AxiosResponse<Workspace> = await apiClient.get(WS_ENDPOINTS.GET(id));
  return response.data;
}

export async function deleteWorkspace(id: string): Promise<void> {
  await apiClient.delete(WS_ENDPOINTS.DELETE(id));
}

export async function inviteMember(workspaceId: string, email: string, role: string = 'viewer'): Promise<WorkspaceMember> {
  const response: AxiosResponse<WorkspaceMember> = await apiClient.post(
    WS_ENDPOINTS.INVITE(workspaceId),
    { email, role }
  );
  return response.data;
}

export async function listMembers(workspaceId: string): Promise<WorkspaceMember[]> {
  const response: AxiosResponse<WorkspaceMember[]> = await apiClient.get(WS_ENDPOINTS.MEMBERS(workspaceId));
  return response.data;
}

export async function removeMember(workspaceId: string, userId: string): Promise<void> {
  await apiClient.delete(WS_ENDPOINTS.REMOVE_MEMBER(workspaceId, userId));
}

export async function listSharedItems(workspaceId: string): Promise<SharedItem[]> {
  const response: AxiosResponse<SharedItem[]> = await apiClient.get(WS_ENDPOINTS.ITEMS(workspaceId));
  return response.data;
}

export async function addComment(itemId: string, content: string): Promise<WorkspaceComment> {
  const response: AxiosResponse<WorkspaceComment> = await apiClient.post(
    WS_ENDPOINTS.COMMENTS(itemId),
    { content }
  );
  return response.data;
}

export async function listComments(itemId: string): Promise<WorkspaceComment[]> {
  const response: AxiosResponse<WorkspaceComment[]> = await apiClient.get(WS_ENDPOINTS.COMMENTS(itemId));
  return response.data;
}

export const workspaceApi = {
  listWorkspaces, createWorkspace, getWorkspace, deleteWorkspace,
  inviteMember, listMembers, removeMember, listSharedItems,
  addComment, listComments,
} as const;

export default workspaceApi;
