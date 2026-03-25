"""
Security Guardian service - AI safety, PII detection, guardrails, and audit trails.

Provides content scanning, prompt injection detection, PII redaction,
configurable guardrail rules, and comprehensive audit logging.
"""

import json
import re
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.security_guardian import (
    AuditAction,
    AuditLog,
    GuardrailRule,
    ScanStatus,
    SecurityScan,
    SeverityLevel,
)

logger = structlog.get_logger()

# PII detection patterns
PII_PATTERNS = {
    "email": {
        "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "severity": "high",
        "description": "Email address detected",
    },
    "phone": {
        "pattern": r'\b(?:\+?[1-9]\d{0,2}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b',
        "severity": "high",
        "description": "Phone number detected",
    },
    "ssn": {
        "pattern": r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',
        "severity": "critical",
        "description": "Social Security Number pattern detected",
    },
    "credit_card": {
        "pattern": r'\b(?:4\d{3}|5[1-5]\d{2}|6011|3[47]\d{2})[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b',
        "severity": "critical",
        "description": "Credit card number pattern detected",
    },
    "ip_address": {
        "pattern": r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b',
        "severity": "medium",
        "description": "IP address detected",
    },
    "iban": {
        "pattern": r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]?\d{0,16})?\b',
        "severity": "critical",
        "description": "IBAN number detected",
    },
    "french_id": {
        "pattern": r'\b\d{13,15}\b',
        "severity": "high",
        "description": "French national ID / INSEE number pattern",
    },
}

# Prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions",
    r"disregard\s+(?:all\s+)?(?:previous|prior)\s+(?:instructions|rules)",
    r"you\s+are\s+now\s+(?:a|an)\s+(?:different|new)",
    r"forget\s+(?:all|everything|your)\s+(?:instructions|rules|training)",
    r"pretend\s+(?:you\s+are|to\s+be)",
    r"act\s+as\s+(?:if|though)\s+you",
    r"bypass\s+(?:your|all|any)\s+(?:restrictions|limitations|filters)",
    r"jailbreak",
    r"DAN\s+mode",
    r"developer\s+mode\s+enabled",
]


class SecurityGuardianService:
    """Service for AI security, PII detection, and audit trails."""

    @staticmethod
    async def scan_content(
        user_id: UUID, text: str, scan_types: list[str],
        auto_redact: bool, target_type: str,
        target_id: Optional[str], session: AsyncSession,
    ) -> SecurityScan:
        """Scan content for PII, prompt injection, and safety issues."""
        scan = SecurityScan(
            user_id=user_id,
            scan_type=",".join(scan_types),
            target_type=target_type,
            target_id=target_id,
            content_preview=text[:500],
            status=ScanStatus.SCANNING,
        )
        session.add(scan)
        await session.flush()

        findings = []

        # PII Detection (Presidio if available, else regex fallback)
        if "pii" in scan_types:
            pii_findings = SecurityGuardianService._detect_pii_smart(text)
            findings.extend(pii_findings)

        # Prompt Injection Detection (NeMo advanced + regex)
        if "prompt_injection" in scan_types:
            # NeMo advanced patterns first (if available)
            try:
                from app.modules.security_guardian.nemo_guardrails import is_available as nemo_avail, check_prompt_injection_advanced
                if nemo_avail():
                    nemo_findings = check_prompt_injection_advanced(text)
                    if nemo_findings:
                        findings.extend(nemo_findings)
            except Exception:
                pass
            # Always run regex patterns as complement
            injection_findings = SecurityGuardianService._detect_prompt_injection(text)
            # Deduplicate: only add regex findings not already caught by NeMo
            nemo_types = {f.get("description", "") for f in findings if f.get("type") == "prompt_injection_advanced"}
            for inj in injection_findings:
                if inj.get("description", "") not in nemo_types:
                    findings.extend([inj])

        # Content Safety (using AI)
        if "content_safety" in scan_types:
            safety_findings = await SecurityGuardianService._check_content_safety(text, user_id)
            findings.extend(safety_findings)

        # Auto-redact PII if requested (Presidio anonymization if available, else regex)
        redacted = None
        if auto_redact and findings:
            redacted = SecurityGuardianService._redact_pii_smart(text, findings)

        # Determine severity
        severity = None
        if findings:
            severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            max_severity = max(findings, key=lambda f: severity_order.get(f.get("severity", "low"), 0))
            severity = max_severity.get("severity")

        scan.findings_json = json.dumps(findings, ensure_ascii=False)
        scan.findings_count = len(findings)
        scan.severity = SeverityLevel(severity) if severity else None
        scan.auto_redacted = auto_redact and bool(findings)
        scan.redacted_text = redacted
        scan.status = ScanStatus.ISSUES_FOUND if findings else ScanStatus.CLEAN

        session.add(scan)
        await session.commit()
        await session.refresh(scan)

        logger.info(
            "security_scan_complete",
            scan_id=str(scan.id),
            findings_count=len(findings),
            severity=severity,
        )
        return scan

    @staticmethod
    def _detect_pii_smart(text: str) -> list[dict]:
        """Smart PII detection: uses Presidio if available, falls back to regex.

        Presidio detects names, organizations, locations (NLP-based) in addition
        to patterns. Regex is always run as a complement for custom patterns.
        """
        findings = []

        # Try Presidio first (enterprise-grade NLP detection)
        try:
            from app.modules.security_guardian.presidio_service import is_available, detect_pii
            if is_available():
                presidio_findings = detect_pii(text)
                if presidio_findings:
                    findings.extend(presidio_findings)
                    logger.debug("presidio_pii_detected", count=len(presidio_findings))
        except Exception as e:
            logger.debug("presidio_fallback", error=str(e))

        # Always run regex as complement (catches custom patterns Presidio might miss)
        regex_findings = SecurityGuardianService._detect_pii(text)

        # Merge: add regex findings that Presidio didn't catch (avoid duplicates by location)
        presidio_locations = {f.get("location") for f in findings if f.get("location")}
        for rf in regex_findings:
            if rf.get("location") not in presidio_locations:
                findings.append(rf)

        return findings

    @staticmethod
    def _redact_pii_smart(text: str, findings: list[dict]) -> str:
        """Smart redaction: uses Presidio anonymizer if available, else regex.

        Presidio provides reversible anonymization mapping.
        """
        try:
            from app.modules.security_guardian.presidio_service import is_available, anonymize
            if is_available():
                anonymized_text, mapping = anonymize(text)
                if anonymized_text != text:
                    return anonymized_text
        except Exception:
            pass

        # Fallback: regex-based redaction (original implementation)
        return SecurityGuardianService._redact_pii(text, findings)

    @staticmethod
    def _detect_pii(text: str) -> list[dict]:
        """Detect PII patterns in text using regex (legacy, always available)."""
        findings = []
        for pii_type, config in PII_PATTERNS.items():
            matches = re.finditer(config["pattern"], text, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                findings.append({
                    "type": f"pii_{pii_type}",
                    "severity": config["severity"],
                    "description": config["description"],
                    "location": f"chars {match.start()}-{match.end()}",
                    "suggestion": f"Redact or remove the {pii_type.replace('_', ' ')}",
                })
        return findings

    @staticmethod
    def _detect_prompt_injection(text: str) -> list[dict]:
        """Detect prompt injection attempts."""
        findings = []
        text_lower = text.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                findings.append({
                    "type": "prompt_injection",
                    "severity": "critical",
                    "description": f"Potential prompt injection detected: pattern '{pattern[:50]}'",
                    "location": None,
                    "suggestion": "Block this prompt or sanitize the input",
                })
        return findings

    @staticmethod
    async def _check_content_safety(text: str, user_id: UUID) -> list[dict]:
        """Use AI to check content safety."""
        findings = []
        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"""Analyze this text for safety issues. Check for:
1. Harmful/dangerous instructions
2. Hate speech or discrimination
3. Personal threats
4. Illegal activity instructions

Text: {text[:5000]}

Respond with a JSON array of findings. Each finding: {{"type": "unsafe_content", "severity": "low/medium/high/critical", "description": "what was found"}}
If the text is safe, respond with: []
Respond ONLY with the JSON array.""",
                task="safety_check",
                provider_name="gemini",
                user_id=user_id,
                module="security_guardian",
            )
            response = result.get("processed_text", "[]")
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                parsed = json.loads(response[start:end])
                if isinstance(parsed, list):
                    for f in parsed:
                        if isinstance(f, dict) and f.get("type"):
                            findings.append({
                                "type": f.get("type", "unsafe_content"),
                                "severity": f.get("severity", "medium"),
                                "description": f.get("description", ""),
                                "location": None,
                                "suggestion": "Review and moderate this content",
                            })
        except Exception as e:
            logger.warning("content_safety_check_failed", error=str(e))
        return findings

    @staticmethod
    def _redact_pii(text: str, findings: list[dict]) -> str:
        """Redact detected PII from text."""
        redacted = text
        for pii_type, config in PII_PATTERNS.items():
            label = f"[{pii_type.upper()}_REDACTED]"
            redacted = re.sub(config["pattern"], label, redacted, flags=re.IGNORECASE)
        return redacted

    @staticmethod
    async def log_audit(
        user_id: UUID, action: str, module: str,
        session: AsyncSession,
        provider: Optional[str] = None, model: Optional[str] = None,
        input_preview: Optional[str] = None, output_preview: Optional[str] = None,
        tokens_used: int = 0, cost_usd: float = 0.0,
        ip_address: Optional[str] = None, user_agent: Optional[str] = None,
        metadata: Optional[dict] = None, risk_level: Optional[str] = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        log = AuditLog(
            user_id=user_id,
            action=AuditAction(action) if action in [a.value for a in AuditAction] else AuditAction.AI_QUERY,
            module=module,
            provider=provider,
            model=model,
            input_preview=input_preview[:500] if input_preview else None,
            output_preview=output_preview[:500] if output_preview else None,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            ip_address=ip_address,
            user_agent=user_agent[:300] if user_agent else None,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
            risk_level=SeverityLevel(risk_level) if risk_level else None,
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log

    @staticmethod
    async def get_audit_logs(
        user_id: UUID, session: AsyncSession,
        module: Optional[str] = None, action: Optional[str] = None,
        flagged_only: bool = False, limit: int = 50, skip: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs with filters."""
        query = select(AuditLog).where(AuditLog.user_id == user_id)
        if module:
            query = query.where(AuditLog.module == module)
        if action:
            query = query.where(AuditLog.action == action)
        if flagged_only:
            query = query.where(AuditLog.flagged == True)
        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_guardrail(
        user_id: UUID, name: str, description: Optional[str],
        rule_type: str, config: dict, action: str, severity: str,
        session: AsyncSession,
    ) -> GuardrailRule:
        """Create a guardrail rule."""
        rule = GuardrailRule(
            user_id=user_id,
            name=name,
            description=description,
            rule_type=rule_type,
            config_json=json.dumps(config, ensure_ascii=False),
            action=action,
            severity=SeverityLevel(severity) if severity in [s.value for s in SeverityLevel] else SeverityLevel.MEDIUM,
        )
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return rule

    @staticmethod
    async def list_guardrails(user_id: UUID, session: AsyncSession) -> list[GuardrailRule]:
        result = await session.execute(
            select(GuardrailRule).where(GuardrailRule.user_id == user_id)
            .order_by(GuardrailRule.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_guardrail(
        rule_id: UUID, user_id: UUID, updates: dict, session: AsyncSession,
    ) -> Optional[GuardrailRule]:
        rule = await session.get(GuardrailRule, rule_id)
        if not rule or rule.user_id != user_id:
            return None
        if "name" in updates and updates["name"]:
            rule.name = updates["name"]
        if "description" in updates:
            rule.description = updates["description"]
        if "config" in updates and updates["config"] is not None:
            rule.config_json = json.dumps(updates["config"], ensure_ascii=False)
        if "enabled" in updates and updates["enabled"] is not None:
            rule.enabled = updates["enabled"]
        if "action" in updates and updates["action"]:
            rule.action = updates["action"]
        if "severity" in updates and updates["severity"]:
            rule.severity = SeverityLevel(updates["severity"])
        rule.updated_at = datetime.utcnow()
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return rule

    @staticmethod
    async def delete_guardrail(rule_id: UUID, user_id: UUID, session: AsyncSession) -> bool:
        rule = await session.get(GuardrailRule, rule_id)
        if not rule or rule.user_id != user_id:
            return False
        await session.delete(rule)
        await session.commit()
        return True

    @staticmethod
    async def get_dashboard(user_id: UUID, session: AsyncSession) -> dict:
        """Get security dashboard overview."""
        # Count scans
        total_scans = (await session.execute(
            select(func.count()).select_from(SecurityScan).where(SecurityScan.user_id == user_id)
        )).scalar_one()

        issues_found = (await session.execute(
            select(func.count()).select_from(SecurityScan).where(
                SecurityScan.user_id == user_id, SecurityScan.status == ScanStatus.ISSUES_FOUND
            )
        )).scalar_one()

        # Count audit entries
        audit_entries = (await session.execute(
            select(func.count()).select_from(AuditLog).where(AuditLog.user_id == user_id)
        )).scalar_one()

        # PII and blocked counts
        pii_scans = await session.execute(
            select(SecurityScan).where(
                SecurityScan.user_id == user_id,
                SecurityScan.status == ScanStatus.ISSUES_FOUND,
            ).order_by(SecurityScan.created_at.desc()).limit(10)
        )
        recent_scans = list(pii_scans.scalars().all())

        pii_count = 0
        blocked_count = 0
        recent_findings = []
        risk_dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for s in recent_scans:
            findings = json.loads(s.findings_json) if s.findings_json else []
            for f in findings:
                if f.get("type", "").startswith("pii_"):
                    pii_count += 1
                if f.get("type") == "prompt_injection":
                    blocked_count += 1
                sev = f.get("severity", "low")
                if sev in risk_dist:
                    risk_dist[sev] += 1
                recent_findings.append(f)

        # Top modules
        module_counts = await session.execute(
            select(AuditLog.module, func.count().label("count"))
            .where(AuditLog.user_id == user_id)
            .group_by(AuditLog.module)
            .order_by(func.count().desc())
            .limit(5)
        )
        top_modules = [{"module": row[0], "count": row[1]} for row in module_counts]

        return {
            "total_scans": total_scans,
            "issues_found": issues_found,
            "pii_detected": pii_count,
            "prompts_blocked": blocked_count,
            "audit_entries": audit_entries,
            "risk_distribution": risk_dist,
            "recent_findings": recent_findings[:10],
            "top_modules": top_modules,
        }
