/**
 * Content Studio hooks
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createProject,
  deleteProject,
  generateContents,
  getProjectContents,
  listFormats,
  listProjects,
  regenerateContent,
  updateContent,
} from '../api';
import type {
  ContentProject,
  ContentUpdateRequest,
  GenerateRequest,
  GeneratedContent,
  ProjectCreateRequest,
} from '../types';

export function useProjects() {
  return useQuery<ContentProject[]>({
    queryKey: ['content-studio', 'projects'],
    queryFn: listProjects,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation<ContentProject, Error, ProjectCreateRequest>({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-studio', 'projects'] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-studio', 'projects'] });
    },
  });
}

export function useGenerateContents(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation<GeneratedContent[], Error, GenerateRequest>({
    mutationFn: (data) => generateContents(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-studio', 'contents', projectId] });
    },
  });
}

export function useProjectContents(projectId: string | null) {
  return useQuery<GeneratedContent[]>({
    queryKey: ['content-studio', 'contents', projectId],
    queryFn: () => getProjectContents(projectId!),
    enabled: !!projectId,
  });
}

export function useUpdateContent() {
  const queryClient = useQueryClient();
  return useMutation<GeneratedContent, Error, { id: string; data: ContentUpdateRequest }>({
    mutationFn: ({ id, data }) => updateContent(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-studio'] });
    },
  });
}

export function useRegenerateContent() {
  const queryClient = useQueryClient();
  return useMutation<GeneratedContent, Error, { id: string; instructions?: string }>({
    mutationFn: ({ id, instructions }) => regenerateContent(id, { custom_instructions: instructions }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-studio'] });
    },
  });
}

export function useFormats() {
  return useQuery({
    queryKey: ['content-studio', 'formats'],
    queryFn: listFormats,
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}
