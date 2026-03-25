/**
 * Social Publisher hooks
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  connectAccount,
  createPost,
  deletePost,
  disconnectAccount,
  getPost,
  getPostAnalytics,
  listAccounts,
  listPlatforms,
  listPosts,
  publishPost,
  recycleContent,
  schedulePost,
} from '../api';
import type {
  PostAnalytics,
  PostCreateRequest,
  PostListResponse,
  RecycleRequest,
  SocialAccount,
  SocialAccountCreateRequest,
  SocialPost,
} from '../types';

// -- Account hooks --

export function useAccounts() {
  return useQuery<SocialAccount[]>({
    queryKey: ['social-publisher', 'accounts'],
    queryFn: listAccounts,
  });
}

export function useConnectAccount() {
  const queryClient = useQueryClient();
  return useMutation<SocialAccount, Error, SocialAccountCreateRequest>({
    mutationFn: connectAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-publisher', 'accounts'] });
    },
  });
}

export function useDisconnectAccount() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: disconnectAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-publisher', 'accounts'] });
    },
  });
}

// -- Post hooks --

export function usePosts(params?: { status?: string; limit?: number; offset?: number }) {
  return useQuery<PostListResponse>({
    queryKey: ['social-publisher', 'posts', params],
    queryFn: () => listPosts(params),
  });
}

export function usePost(postId: string | null) {
  return useQuery<SocialPost>({
    queryKey: ['social-publisher', 'post', postId],
    queryFn: () => getPost(postId!),
    enabled: !!postId,
  });
}

export function useCreatePost() {
  const queryClient = useQueryClient();
  return useMutation<SocialPost, Error, PostCreateRequest>({
    mutationFn: createPost,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-publisher', 'posts'] });
    },
  });
}

export function usePublishPost() {
  const queryClient = useQueryClient();
  return useMutation<SocialPost, Error, string>({
    mutationFn: publishPost,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-publisher', 'posts'] });
    },
  });
}

export function useSchedulePost() {
  const queryClient = useQueryClient();
  return useMutation<SocialPost, Error, { postId: string; schedule_at: string }>({
    mutationFn: ({ postId, schedule_at }) => schedulePost(postId, schedule_at),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-publisher', 'posts'] });
    },
  });
}

export function useDeletePost() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deletePost,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-publisher', 'posts'] });
    },
  });
}

export function usePostAnalytics(postId: string | null) {
  return useQuery<PostAnalytics[]>({
    queryKey: ['social-publisher', 'analytics', postId],
    queryFn: () => getPostAnalytics(postId!),
    enabled: !!postId,
  });
}

export function useRecycleContent() {
  const queryClient = useQueryClient();
  return useMutation<SocialPost, Error, RecycleRequest>({
    mutationFn: recycleContent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-publisher', 'posts'] });
    },
  });
}

export function usePlatforms() {
  return useQuery({
    queryKey: ['social-publisher', 'platforms'],
    queryFn: listPlatforms,
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}
