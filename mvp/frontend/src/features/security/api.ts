import apiClient from '@/lib/apiClient';
import type { AuditLog, GuardrailRule, ScanRequest, SecurityDashboard, SecurityScan } from './types';

export const scanContent = async (data: ScanRequest): Promise<SecurityScan> => (await apiClient.post('/api/security/scan', data)).data;
export const getDashboard = async (): Promise<SecurityDashboard> => (await apiClient.get('/api/security/dashboard')).data;
export const listAuditLogs = async (params?: { module?: string; flagged_only?: boolean; limit?: number }): Promise<AuditLog[]> =>
  (await apiClient.get('/api/security/audit', { params })).data;
export const listGuardrails = async (): Promise<GuardrailRule[]> => (await apiClient.get('/api/security/guardrails')).data;
export const createGuardrail = async (data: { name: string; rule_type: string; config: Record<string, unknown>; action?: string; severity?: string }): Promise<GuardrailRule> =>
  (await apiClient.post('/api/security/guardrails', data)).data;
export const deleteGuardrail = async (id: string): Promise<void> => { await apiClient.delete(`/api/security/guardrails/${id}`); };
