export interface ScanFinding {
  type: string; severity: string; description: string;
  location: string | null; suggestion: string | null;
}
export interface SecurityScan {
  id: string; scan_type: string; target_type: string; status: string;
  findings: ScanFinding[]; findings_count: number; severity: string | null;
  auto_redacted: boolean; redacted_text: string | null; created_at: string;
}
export interface AuditLog {
  id: string; user_id: string; action: string; module: string;
  provider: string | null; model: string | null;
  input_preview: string | null; output_preview: string | null;
  tokens_used: number; cost_usd: number;
  risk_level: string | null; flagged: boolean; created_at: string;
}
export interface GuardrailRule {
  id: string; user_id: string; name: string; description: string | null;
  rule_type: string; config_json: string; enabled: boolean;
  action: string; severity: string; triggers_count: number;
  created_at: string; updated_at: string;
}
export interface SecurityDashboard {
  total_scans: number; issues_found: number; pii_detected: number;
  prompts_blocked: number; audit_entries: number;
  risk_distribution: Record<string, number>;
  recent_findings: ScanFinding[]; top_modules: { module: string; count: number }[];
}
export interface ScanRequest {
  text: string; scan_types?: string[]; auto_redact?: boolean;
  target_type?: string;
}
