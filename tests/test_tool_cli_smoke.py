from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from uuid import uuid4


try:
    from app import cli as cli_module
    from app import main as main_module
    from tests.runtime_test_utils import reset_runtime_state
except Exception as exc:  # pragma: no cover - environment dependent
    cli_module = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(cli_module is None, f"runtime dependencies unavailable: {IMPORT_ERROR}")
class TestToolCliSmoke(unittest.TestCase):
    def setUp(self) -> None:
        reset_runtime_state(main_module)

    def _run_cli_json(self, *args: str) -> tuple[int, dict[str, object]]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = cli_module.main([*args, "--json"])
        payload = json.loads(stdout.getvalue().strip() or "{}")
        return exit_code, payload

    def test_submit_status_and_events_commands(self) -> None:
        exit_code, submit_payload = self._run_cli_json(
            "submit",
            "--requested-by",
            "qa_user",
            "--task-kind",
            "task",
            "--request-text",
            "주간 운영회의 메모를 요약하고 액션 아이템을 정리해줘",
            "--metadata-json",
            json.dumps(
                {
                    "meeting_title": "ops sync",
                    "meeting_date": "2026-03-12",
                    "participants": ["Kim"],
                    "notes": "internal only",
                },
                ensure_ascii=False,
            ),
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(submit_payload["resolved_kind"], "task")
        self.assertEqual(submit_payload["status"], "DONE")
        task_id = str(submit_payload["task_id"])

        exit_code, status_payload = self._run_cli_json("status", "--task-id", task_id, "--actor-id", "qa_user")
        self.assertEqual(exit_code, 0)
        self.assertEqual(status_payload["status"], "DONE")

        exit_code, events_payload = self._run_cli_json("events", "--task-id", task_id, "--actor-id", "qa_user")
        self.assertEqual(exit_code, 0)
        self.assertGreaterEqual(int(events_payload["count"]), 3)
        event_types = {item["event_type"] for item in events_payload["items"]}
        self.assertIn("AGENT_ROUTED", event_types)
        self.assertIn("TASK_CREATED", event_types)

    def test_tools_command_lists_registered_tools(self) -> None:
        exit_code, payload = self._run_cli_json("tools", "--actor-id", "qa_user")
        self.assertEqual(exit_code, 0)
        self.assertGreaterEqual(int(payload["count"]), 6)
        tool_ids = {item["tool_id"] for item in payload["items"]}
        self.assertIn("internal.summary.generate", tool_ids)
        self.assertIn("redmine.issue.create", tool_ids)

    def test_approve_command_resumes_pending_task(self) -> None:
        exit_code, submit_payload = self._run_cli_json(
            "submit",
            "--requested-by",
            "qa_user",
            "--task-kind",
            "task",
            "--request-text",
            "요약 결과를 외부 전송 해주세요",
            "--metadata-json",
            json.dumps(
                {
                    "meeting_title": "approval-needed",
                    "meeting_date": "2026-03-12",
                    "participants": ["Ops"],
                    "notes": "요약 결과를 외부 전송 해주세요",
                },
                ensure_ascii=False,
            ),
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(submit_payload["status"], "NEEDS_HUMAN_APPROVAL")
        queue_id = str(submit_payload["approval_queue_id"])
        task_id = str(submit_payload["task_id"])

        exit_code, approve_payload = self._run_cli_json(
            "approve",
            "--queue-id",
            queue_id,
            "--acted-by",
            "qa_approver",
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(approve_payload["status"], "APPROVED")

        exit_code, status_payload = self._run_cli_json("status", "--task-id", task_id, "--actor-id", "qa_user")
        self.assertEqual(exit_code, 0)
        self.assertEqual(status_payload["status"], "DONE")

    def test_reject_command_finishes_task(self) -> None:
        exit_code, submit_payload = self._run_cli_json(
            "submit",
            "--requested-by",
            "qa_user",
            "--task-kind",
            "task",
            "--request-text",
            "요약 결과를 외부 전송 해주세요",
            "--metadata-json",
            json.dumps(
                {
                    "meeting_title": "reject-needed",
                    "meeting_date": "2026-03-12",
                    "participants": ["Ops"],
                    "notes": "요약 결과를 외부 전송 해주세요",
                },
                ensure_ascii=False,
            ),
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(submit_payload["status"], "NEEDS_HUMAN_APPROVAL")
        queue_id = str(submit_payload["approval_queue_id"])
        task_id = str(submit_payload["task_id"])

        exit_code, reject_payload = self._run_cli_json(
            "reject",
            "--queue-id",
            queue_id,
            "--acted-by",
            "qa_approver",
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(reject_payload["status"], "REJECTED")
        self.assertEqual(reject_payload["task_status"], "DONE")

        exit_code, status_payload = self._run_cli_json("status", "--task-id", task_id, "--actor-id", "qa_user")
        self.assertEqual(exit_code, 0)
        self.assertEqual(status_payload["status"], "DONE")
        self.assertEqual(status_payload["final_reason"], "rejected_by_human")

    def test_script_entrypoint_executes_as_python_app_cli(self) -> None:
        db_path = f"/tmp/nestclaw-stage8-tool-cli-{uuid4().hex}.db"
        env = os.environ.copy()
        env["NEWCLAW_DB_PATH"] = db_path
        repo_root = Path(__file__).resolve().parents[1]

        completed = subprocess.run(
            [
                sys.executable,
                "app/cli.py",
                "submit",
                "--requested-by",
                "qa_user",
                "--task-kind",
                "task",
                "--request-text",
                "운영회의 요약",
                "--metadata-json",
                json.dumps(
                    {
                        "meeting_title": "ops sync",
                        "meeting_date": "2026-03-12",
                        "participants": ["Kim"],
                        "notes": "internal only",
                    },
                    ensure_ascii=False,
                ),
                "--json",
            ],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout.strip() or "{}")
        self.assertEqual(payload["status"], "DONE")
        self.assertEqual(payload["resolved_kind"], "task")


if __name__ == "__main__":
    unittest.main()
