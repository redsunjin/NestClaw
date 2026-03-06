from __future__ import annotations

import unittest

from app.incident_policy import (
    IncidentPolicyDecision,
    approval_reason_for_risk,
    approval_rule_for_risk,
    evaluate_incident_action_policy,
    normalize_incident_risk_level,
)


def _action_card(
    *,
    risk_level: str = "medium",
    evidence_links: list[str] | None = None,
    method: str = "issue.create",
    payload: dict[str, str] | None = None,
) -> dict[str, object]:
    return {
        "action_id": "act_test",
        "incident_id": "inc_test",
        "action_type": "redmine_issue_create",
        "risk_level": risk_level,
        "approval_required": risk_level in {"high", "critical"},
        "evidence_links": evidence_links if evidence_links is not None else ["runbook://billing/cache"],
        "mcp_call": {
            "method": method,
            "payload": payload or {"subject": "incident update", "description": "internal note"},
        },
    }


class TestIncidentPolicyGate(unittest.TestCase):
    def test_unknown_risk_defaults_to_medium(self) -> None:
        self.assertEqual(normalize_incident_risk_level("unknown"), "medium")
        self.assertEqual(approval_rule_for_risk("unknown").risk_level, "medium")
        self.assertIsNone(approval_reason_for_risk("unknown"))

    def test_low_risk_with_evidence_is_auto_approved(self) -> None:
        decision = evaluate_incident_action_policy(
            _action_card(risk_level="low"),
            summary="internal incident summary",
        )

        self.assertEqual(decision.gate_status, "APPROVED")
        self.assertEqual(decision.risk_level, "low")
        self.assertEqual(decision.review_recommendation, "auto_execute_allowed")

    def test_missing_evidence_requires_approval_even_for_medium_risk(self) -> None:
        decision = evaluate_incident_action_policy(
            _action_card(risk_level="medium", evidence_links=[]),
            summary="internal incident summary",
        )

        self.assertEqual(decision.gate_status, "NEEDS_APPROVAL")
        self.assertEqual(decision.reason_code, "missing_evidence")
        self.assertEqual(decision.reason_message, "incident action requires evidence before auto execution")

    def test_high_risk_requires_single_approver(self) -> None:
        decision = evaluate_incident_action_policy(
            _action_card(risk_level="high"),
            summary="customer-facing outage requires restart review",
        )

        self.assertEqual(decision.gate_status, "NEEDS_APPROVAL")
        self.assertEqual(decision.reason_code, "high_risk_action")
        self.assertEqual(decision.review_recommendation, "single_approver_required")
        self.assertEqual(decision.approver_group, "ops_team")

    def test_critical_risk_recommends_two_person_review(self) -> None:
        decision = evaluate_incident_action_policy(
            _action_card(risk_level="critical"),
            summary="critical incident with rollback implications",
        )

        self.assertEqual(decision.gate_status, "NEEDS_APPROVAL")
        self.assertEqual(decision.reason_code, "critical_risk_action")
        self.assertEqual(decision.review_recommendation, "two_person_review_recommended")

    def test_policy_block_wins_over_risk_gate(self) -> None:
        decision = evaluate_incident_action_policy(
            _action_card(
                risk_level="low",
                payload={"subject": "incident update", "description": "send externally to customer"},
            ),
            summary="Please external send the report",
        )

        self.assertEqual(decision.gate_status, "BLOCKED_POLICY")
        self.assertEqual(decision.reason_code, "external_send_requested")
        self.assertIn("policy gate", decision.reason_message or "")

    def test_approved_reasons_can_bypass_policy_and_risk_gate(self) -> None:
        decision = evaluate_incident_action_policy(
            _action_card(
                risk_level="critical",
                evidence_links=["runbook://critical"],
                payload={"subject": "incident update", "description": "send externally to customer"},
            ),
            summary="Please external send the report",
            approved_reasons={"external_send_requested", "critical_risk_action"},
        )

        self.assertEqual(decision, IncidentPolicyDecision(
            gate_status="APPROVED",
            risk_level="critical",
            approver_group="ops_team",
            review_recommendation="two_person_review_recommended",
        ))


if __name__ == "__main__":
    unittest.main()
