'use client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createGuardrail, deleteGuardrail, getDashboard, listAuditLogs, listGuardrails, scanContent } from '../api';
import type { AuditLog, GuardrailRule, ScanRequest, SecurityDashboard, SecurityScan } from '../types';

export function useScanContent() {
  return useMutation<SecurityScan, Error, ScanRequest>({ mutationFn: scanContent });
}
export function useSecurityDashboard() {
  return useQuery<SecurityDashboard>({ queryKey: ['security-dashboard'], queryFn: getDashboard });
}
export function useAuditLogs(params?: { module?: string; flagged_only?: boolean }) {
  return useQuery<AuditLog[]>({ queryKey: ['audit-logs', params], queryFn: () => listAuditLogs(params) });
}
export function useGuardrails() {
  return useQuery<GuardrailRule[]>({ queryKey: ['guardrails'], queryFn: listGuardrails });
}
export function useCreateGuardrail() {
  const qc = useQueryClient();
  return useMutation<GuardrailRule, Error, { name: string; rule_type: string; config: Record<string, unknown>; action?: string; severity?: string }>({
    mutationFn: createGuardrail,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['guardrails'] }),
  });
}
export function useDeleteGuardrail() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({ mutationFn: deleteGuardrail, onSuccess: () => qc.invalidateQueries({ queryKey: ['guardrails'] }) });
}
