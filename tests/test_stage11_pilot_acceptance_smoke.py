import subprocess
import unittest
from pathlib import Path


ACCEPTANCE_DOC = Path("NESTCLAW_PILOT_ACCEPTANCE_CYCLE_2026-04-10.md")
VALIDATOR = Path("scripts/validate_pilot_acceptance_cycle.sh")


class TestStage11PilotAcceptanceSmoke(unittest.TestCase):
    def test_acceptance_cycle_doc_contains_canonical_decision_vocab(self) -> None:
        source = ACCEPTANCE_DOC.read_text(encoding="utf-8")
        self.assertIn("Conditional Go", source)
        self.assertIn("NO-GO", source)
        self.assertIn("operational hold", source)
        self.assertIn("agent.handoff", source)
        self.assertIn("BLOCKED", source)
        self.assertIn("FAIL", source)

    def test_validator_reports_ready_even_when_current_decision_is_no_go(self) -> None:
        result = subprocess.run(
            ["bash", str(VALIDATOR), str(ACCEPTANCE_DOC)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("# NestClaw Pilot Acceptance Cycle Validation", result.stdout)
        self.assertIn("- current_pilot_decision: NO-GO for external live pilot", result.stdout)
        self.assertIn("- current_readiness_state: BLOCKED", result.stdout)
        self.assertIn("- status: READY", result.stdout)


if __name__ == "__main__":
    unittest.main()
