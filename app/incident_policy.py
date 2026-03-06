from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


LOW_RISK = "low"
MEDIUM_RISK = "medium"
HIGH_RISK = "high"
CRITICAL_RISK = "critical"
DEFAULT_RISK_LEVEL = MEDIUM_RISK

POLICY_BLOCK_PATTERNS: dict[str, tuple[str, ...]] = {
    "external_send_requested": (
        "외부 전송",
        "external send",
        "메일 발송",
        "send externally",
        "http://",
        "https://",
    )
}


@dataclass(frozen=True)
class IncidentApprovalRule:
    risk_level: str
    requires_approval: bool
    approver_group: str
    review_recommendation: str


@dataclass(frozen=True)
class IncidentPolicyDecision:
    gate_status: str
    risk_level: str
    reason_code: str | None = None
    reason_message: str | None = None
    approver_group: str = "ops_team"
    review_recommendation: str | None = None


INCIDENT_APPROVAL_RULES: dict[str, IncidentApprovalRule] = {
    LOW_RISK: IncidentApprovalRule(
        risk_level=LOW_RISK,
        requires_approval=False,
        approver_group="ops_team",
        review_recommendation="auto_execute_allowed",
    ),
    MEDIUM_RISK: IncidentApprovalRule(
        risk_level=MEDIUM_RISK,
        requires_approval=False,
        approver_group="ops_team",
        review_recommendation="auto_execute_allowed_with_evidence",
    ),
    HIGH_RISK: IncidentApprovalRule(
        risk_level=HIGH_RISK,
        requires_approval=True,
        approver_group="ops_team",
        review_recommendation="single_approver_required",
    ),
    CRITICAL_RISK: IncidentApprovalRule(
        risk_level=CRITICAL_RISK,
        requires_approval=True,
        approver_group="ops_team",
        review_recommendation="two_person_review_recommended",
    ),
}

REASON_MESSAGES: dict[str, str] = {
    "external_send_requested": "external transfer request detected by policy gate",
    "missing_evidence": "incident action requires evidence before auto execution",
    "high_risk_action": "high-risk incident action requires human approval",
    "critical_risk_action": "critical-risk incident action requires human approval",
}


def normalize_incident_risk_level(raw: Any) -> str:
    normalized = str(raw or DEFAULT_RISK_LEVEL).strip().lower()
    if normalized not in INCIDENT_APPROVAL_RULES:
        return DEFAULT_RISK_LEVEL
    return normalized


def approval_rule_for_risk(risk_level: Any) -> IncidentApprovalRule:
    return INCIDENT_APPROVAL_RULES[normalize_incident_risk_level(risk_level)]


def requires_human_approval(risk_level: Any) -> bool:
    return approval_rule_for_risk(risk_level).requires_approval


def approval_reason_for_risk(risk_level: Any) -> str | None:
    normalized = normalize_incident_risk_level(risk_level)
    if normalized == HIGH_RISK:
        return "high_risk_action"
    if normalized == CRITICAL_RISK:
        return "critical_risk_action"
    return None


def reason_message_for(reason_code: str) -> str:
    return REASON_MESSAGES.get(reason_code, f"approval required: {reason_code}")


def detect_policy_block(
    task_input: Mapping[str, Any],
    approved_reasons: set[str],
    *,
    block_patterns: Mapping[str, tuple[str, ...]] | None = None,
) -> str | None:
    patterns_map = block_patterns or POLICY_BLOCK_PATTERNS
    joined = " ".join(str(value) for value in task_input.values()).lower()
    for reason_code, patterns in patterns_map.items():
        if reason_code in approved_reasons:
            continue
        if any(pattern.lower() in joined for pattern in patterns):
            return reason_code
    return None


def evaluate_incident_action_policy(
    action_card: Mapping[str, Any],
    *,
    summary: str,
    approved_reasons: set[str] | None = None,
    policy_profile: str | None = None,
    block_patterns: Mapping[str, tuple[str, ...]] | None = None,
) -> IncidentPolicyDecision:
    approved = set(approved_reasons or set())
    risk_level = normalize_incident_risk_level(action_card.get("risk_level"))
    rule = approval_rule_for_risk(risk_level)

    reason_code = detect_policy_block(
        {
            "summary": summary,
            "method": action_card.get("mcp_call", {}).get("method"),
            "payload": action_card.get("mcp_call", {}).get("payload"),
            "policy_profile": policy_profile or "default",
        },
        approved,
        block_patterns=block_patterns,
    )
    if reason_code:
        return IncidentPolicyDecision(
            gate_status="BLOCKED_POLICY",
            risk_level=risk_level,
            reason_code=reason_code,
            reason_message=reason_message_for(reason_code),
            approver_group=rule.approver_group,
            review_recommendation=rule.review_recommendation,
        )

    evidence_links = [str(item).strip() for item in action_card.get("evidence_links", []) if str(item).strip()]
    if not evidence_links and "missing_evidence" not in approved:
        return IncidentPolicyDecision(
            gate_status="NEEDS_APPROVAL",
            risk_level=risk_level,
            reason_code="missing_evidence",
            reason_message=reason_message_for("missing_evidence"),
            approver_group=rule.approver_group,
            review_recommendation=rule.review_recommendation,
        )

    risk_reason = approval_reason_for_risk(risk_level)
    if risk_reason and risk_reason not in approved:
        return IncidentPolicyDecision(
            gate_status="NEEDS_APPROVAL",
            risk_level=risk_level,
            reason_code=risk_reason,
            reason_message=reason_message_for(risk_reason),
            approver_group=rule.approver_group,
            review_recommendation=rule.review_recommendation,
        )

    return IncidentPolicyDecision(
        gate_status="APPROVED",
        risk_level=risk_level,
        approver_group=rule.approver_group,
        review_recommendation=rule.review_recommendation,
    )
