/**
 * AI Forms hooks
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  closeForm,
  createForm,
  deleteForm,
  generateForm,
  getAnalytics,
  getForm,
  listForms,
  listResponses,
  publishForm,
  scoreResponse,
  updateForm,
} from '../api';
import type {
  Form,
  FormAnalysis,
  FormCreateRequest,
  FormGenerateRequest,
  FormResponseItem,
  FormUpdateRequest,
} from '../types';

export function useForms() {
  return useQuery<Form[]>({
    queryKey: ['forms'],
    queryFn: listForms,
  });
}

export function useForm(id: string | null) {
  return useQuery<Form>({
    queryKey: ['forms', id],
    queryFn: () => getForm(id!),
    enabled: !!id,
  });
}

export function useCreateForm() {
  const queryClient = useQueryClient();
  return useMutation<Form, Error, FormCreateRequest>({
    mutationFn: createForm,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forms'] });
    },
  });
}

export function useUpdateForm() {
  const queryClient = useQueryClient();
  return useMutation<Form, Error, { id: string; data: FormUpdateRequest }>({
    mutationFn: ({ id, data }) => updateForm(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forms'] });
    },
  });
}

export function useDeleteForm() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteForm,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forms'] });
    },
  });
}

export function usePublishForm() {
  const queryClient = useQueryClient();
  return useMutation<Form, Error, string>({
    mutationFn: publishForm,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forms'] });
    },
  });
}

export function useCloseForm() {
  const queryClient = useQueryClient();
  return useMutation<Form, Error, string>({
    mutationFn: closeForm,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forms'] });
    },
  });
}

export function useGenerateForm() {
  const queryClient = useQueryClient();
  return useMutation<Form, Error, FormGenerateRequest>({
    mutationFn: generateForm,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forms'] });
    },
  });
}

export function useFormResponses(formId: string | null) {
  return useQuery<FormResponseItem[]>({
    queryKey: ['forms', formId, 'responses'],
    queryFn: () => listResponses(formId!),
    enabled: !!formId,
  });
}

export function useScoreResponse() {
  const queryClient = useQueryClient();
  return useMutation<FormResponseItem, Error, { formId: string; responseId: string }>({
    mutationFn: ({ formId, responseId }) => scoreResponse(formId, responseId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['forms', variables.formId, 'responses'] });
    },
  });
}

export function useFormAnalytics(formId: string | null) {
  return useQuery<FormAnalysis>({
    queryKey: ['forms', formId, 'analytics'],
    queryFn: () => getAnalytics(formId!),
    enabled: !!formId,
  });
}
