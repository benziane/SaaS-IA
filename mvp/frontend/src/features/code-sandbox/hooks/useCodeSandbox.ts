'use client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  addCell, createSandbox, debugCode, deleteCell, deleteSandbox,
  executeCell, explainCode, generateCode, getSandbox, listSandboxes, updateCell,
} from '../api';
import type { CellResult, CodeDebugResponse, CodeExplainResponse, CodeGenerateResponse, Sandbox } from '../types';

export function useSandboxes() {
  return useQuery<Sandbox[]>({ queryKey: ['sandboxes'], queryFn: listSandboxes });
}

export function useSandbox(id: string | null) {
  return useQuery<Sandbox>({
    queryKey: ['sandbox', id],
    queryFn: () => getSandbox(id!),
    enabled: !!id,
  });
}

export function useCreateSandbox() {
  const qc = useQueryClient();
  return useMutation<Sandbox, Error, { name: string; language?: string; description?: string }>({
    mutationFn: createSandbox,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sandboxes'] }),
  });
}

export function useDeleteSandbox() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteSandbox,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sandboxes'] }),
  });
}

export function useAddCell(sandboxId: string) {
  const qc = useQueryClient();
  return useMutation<Record<string, unknown>, Error, { source: string; cell_type?: string; language?: string }>({
    mutationFn: (data) => addCell(sandboxId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sandbox', sandboxId] }),
  });
}

export function useUpdateCell(sandboxId: string) {
  const qc = useQueryClient();
  return useMutation<Record<string, unknown>, Error, { cellId: string; source: string }>({
    mutationFn: ({ cellId, source }) => updateCell(sandboxId, cellId, source),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sandbox', sandboxId] }),
  });
}

export function useDeleteCell(sandboxId: string) {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (cellId) => deleteCell(sandboxId, cellId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sandbox', sandboxId] }),
  });
}

export function useExecuteCell(sandboxId: string) {
  const qc = useQueryClient();
  return useMutation<CellResult, Error, string>({
    mutationFn: (cellId) => executeCell(sandboxId, cellId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sandbox', sandboxId] }),
  });
}

export function useGenerateCode() {
  return useMutation<CodeGenerateResponse, Error, { prompt: string; language?: string; context?: string }>({
    mutationFn: ({ prompt, language, context }) => generateCode(prompt, language, context),
  });
}

export function useExplainCode() {
  return useMutation<CodeExplainResponse, Error, string>({
    mutationFn: explainCode,
  });
}

export function useDebugCode() {
  return useMutation<CodeDebugResponse, Error, { code: string; error: string }>({
    mutationFn: ({ code, error }) => debugCode(code, error),
  });
}
