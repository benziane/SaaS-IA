/**
 * Workspace Types
 */

export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  is_active: boolean;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMember {
  id: string;
  user_id: string;
  user_email: string;
  role: string;
  joined_at: string;
}

export interface SharedItem {
  id: string;
  item_type: string;
  item_id: string;
  shared_by: string;
  created_at: string;
}

export interface WorkspaceComment {
  id: string;
  user_id: string;
  content: string;
  created_at: string;
}

export interface WorkspaceCreateRequest {
  name: string;
  description?: string;
}

export interface InviteRequest {
  email: string;
  role?: string;
}
