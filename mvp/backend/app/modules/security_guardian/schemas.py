"""
Security Guardian schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    """Request to scan content for security issues."""
    text: str = Field(..., min_length=1, max_length=50000)
    scan_types: list[str] = Field(
        default=["pii", "prompt_injection", "content_safety"],
        description="pii, prompt_injection, content_safety, compliance",
    )
    auto_redact: bool = Field(default=False, description="Automatically redact detected PII")
    target_type: str = Field(default="text", description="text, prompt, transcription, document")
    target_id: Optional[str] = None


class ScanFinding(BaseModel):
    """A single finding from a security scan."""
    type: str  # pii_email, pii_phone, pii_name, prompt_injection, unsafe_content, etc.
    severity: str  # low, medium, high, critical
    description: str
    location: Optional[str] = None  # position or context in text
    suggestion: Optional[str] = None


class ScanRead(BaseModel):
    """Scan result response."""
    id: UUID
    scan_type: str
    target_type: str
    status: str
    findings: list[ScanFinding]
    findings_count: int
    severity: Optional[str]
    auto_redacted: bool
    redacted_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogRead(BaseModel):
    """Audit log entry response."""
    id: UUID
    user_id: UUID
    action: str
    module: str
    provider: Optional[str]
    model: Optional[str]
    input_preview: Optional[str]
    output_preview: Optional[str]
    tokens_used: int
    cost_usd: float
    risk_level: Optional[str]
    flagged: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogFilter(BaseModel):
    """Filter for audit log queries."""
    module: Optional[str] = None
    action: Optional[str] = None
    provider: Optional[str] = None
    flagged_only: bool = False
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class GuardrailRuleCreate(BaseModel):
    """Create a guardrail rule."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    rule_type: str = Field(..., description="block_pattern, pii_redact, content_filter, rate_limit")
    config: dict = Field(default_factory=dict, description="patterns, thresholds, keywords")
    action: str = Field(default="warn", description="warn, block, redact, log")
    severity: str = Field(default="medium", description="low, medium, high, critical")


class GuardrailRuleRead(BaseModel):
    """Guardrail rule response."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    rule_type: str
    config_json: str
    enabled: bool
    action: str
    severity: str
    triggers_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GuardrailRuleUpdate(BaseModel):
    """Update a guardrail rule."""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None
    enabled: Optional[bool] = None
    action: Optional[str] = None
    severity: Optional[str] = None


class SecurityDashboard(BaseModel):
    """Security overview dashboard data."""
    total_scans: int
    issues_found: int
    pii_detected: int
    prompts_blocked: int
    audit_entries: int
    risk_distribution: dict  # low, medium, high, critical counts
    recent_findings: list[ScanFinding]
    top_modules: list[dict]  # module name + count
