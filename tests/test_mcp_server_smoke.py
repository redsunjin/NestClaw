from __future__ import annotations

import json
import os
import select
import subprocess
import sys
import unittest
from pathlib import Path
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[1]


def _encode_message(payload: dict[str, object]) -> bytes:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body


def _readline_with_timeout(stream: object, timeout: float = 5.0) -> bytes:
    ready, _, _ = select.select([stream], [], [], timeout)
    if not ready:
        raise TimeoutError("timed out while waiting for MCP response line")
    return stream.readline()


def _read_message(stream: object, timeout: float = 5.0) -> dict[str, object]:
    headers: dict[str, str] = {}
    while True:
        line = _readline_with_timeout(stream, timeout=timeout)
        if not line:
            raise EOFError("mcp server closed stdout")
        if line in {b"\r\n", b"\n"}:
            break
        name, _, value = line.decode("utf-8").partition(":")
        headers[name.strip().lower()] = value.strip()

    content_length = int(headers["content-length"])
    body = b""
    while len(body) < content_length:
        ready, _, _ = select.select([stream], [], [], timeout)
        if not ready:
            raise TimeoutError("timed out while waiting for MCP response body")
        body += stream.read(content_length - len(body))
    return json.loads(body.decode("utf-8"))


class TestMcpServerSmoke(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = f"/tmp/nestclaw-stage8-mcp-{uuid4().hex}.db"
        env = os.environ.copy()
        env["NEWCLAW_DB_PATH"] = self.db_path
        self.proc = subprocess.Popen(
            [sys.executable, "app/mcp_server.py"],
            cwd=REPO_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            bufsize=0,
        )
        self._initialize()

    def tearDown(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        if self.proc.stdout is not None:
            self.proc.stdout.close()
        if self.proc.stderr is not None:
            self.proc.stderr.close()

    def _send(self, payload: dict[str, object]) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(_encode_message(payload))
        self.proc.stdin.flush()

    def _request(self, payload: dict[str, object]) -> dict[str, object]:
        self._send(payload)
        assert self.proc.stdout is not None
        return _read_message(self.proc.stdout)

    def _initialize(self) -> None:
        response = self._request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "qa", "version": "1.0"},
                },
            }
        )
        self.assertEqual(response["result"]["protocolVersion"], "2025-06-18")
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    def test_tools_list_includes_agent_and_approval_tools(self) -> None:
        response = self._request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = response["result"]["tools"]
        names = {item["name"] for item in tools}
        self.assertEqual(
            names,
            {
                "agent.submit",
                "agent.status",
                "agent.events",
                "approval.list",
                "approval.approve",
                "approval.reject",
            },
        )

    def test_agent_submit_and_status_tool_flow(self) -> None:
        response = self._request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "agent.submit",
                    "arguments": {
                        "request_text": "운영회의 요약",
                        "requested_by": "qa_user",
                        "task_kind": "task",
                        "metadata": {
                            "meeting_title": "ops sync",
                            "meeting_date": "2026-03-12",
                            "participants": ["Kim"],
                            "notes": "internal only",
                        },
                    },
                },
            }
        )
        payload = response["result"]["structuredContent"]
        self.assertEqual(payload["status"], "DONE")
        self.assertEqual(payload["resolved_kind"], "task")
        task_id = payload["task_id"]

        status_response = self._request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "agent.status",
                    "arguments": {"task_id": task_id, "actor_id": "qa_user"},
                },
            }
        )
        self.assertEqual(status_response["result"]["structuredContent"]["status"], "DONE")

    def test_approval_list_and_approve_tool_flow(self) -> None:
        response = self._request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "agent.submit",
                    "arguments": {
                        "request_text": "요약 결과를 외부 전송 해주세요",
                        "requested_by": "qa_user",
                        "task_kind": "task",
                        "metadata": {
                            "meeting_title": "approval-needed",
                            "meeting_date": "2026-03-12",
                            "participants": ["Ops"],
                            "notes": "요약 결과를 외부 전송 해주세요",
                        },
                    },
                },
            }
        )
        payload = response["result"]["structuredContent"]
        self.assertEqual(payload["status"], "NEEDS_HUMAN_APPROVAL")
        queue_id = payload["approval_queue_id"]
        task_id = payload["task_id"]

        list_response = self._request(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "approval.list",
                    "arguments": {"actor_id": "qa_approver", "actor_role": "approver"},
                },
            }
        )
        queue_ids = {item["queue_id"] for item in list_response["result"]["structuredContent"]["items"]}
        self.assertIn(queue_id, queue_ids)

        approve_response = self._request(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {
                    "name": "approval.approve",
                    "arguments": {"queue_id": queue_id, "acted_by": "qa_approver"},
                },
            }
        )
        self.assertEqual(approve_response["result"]["structuredContent"]["status"], "APPROVED")

        status_response = self._request(
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "agent.status",
                    "arguments": {"task_id": task_id, "actor_id": "qa_user"},
                },
            }
        )
        self.assertEqual(status_response["result"]["structuredContent"]["status"], "DONE")

    def test_approval_reject_tool_flow(self) -> None:
        response = self._request(
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {
                    "name": "agent.submit",
                    "arguments": {
                        "request_text": "요약 결과를 외부 전송 해주세요",
                        "requested_by": "qa_user",
                        "task_kind": "task",
                        "metadata": {
                            "meeting_title": "reject-needed",
                            "meeting_date": "2026-03-12",
                            "participants": ["Ops"],
                            "notes": "요약 결과를 외부 전송 해주세요",
                        },
                    },
                },
            }
        )
        payload = response["result"]["structuredContent"]
        self.assertEqual(payload["status"], "NEEDS_HUMAN_APPROVAL")
        queue_id = payload["approval_queue_id"]
        task_id = payload["task_id"]

        reject_response = self._request(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "approval.reject",
                    "arguments": {"queue_id": queue_id, "acted_by": "qa_approver"},
                },
            }
        )
        self.assertEqual(reject_response["result"]["structuredContent"]["status"], "REJECTED")

        status_response = self._request(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "agent.status",
                    "arguments": {"task_id": task_id, "actor_id": "qa_user"},
                },
            }
        )
        final_payload = status_response["result"]["structuredContent"]
        self.assertEqual(final_payload["status"], "DONE")
        self.assertEqual(final_payload["final_reason"], "rejected_by_human")


if __name__ == "__main__":
    unittest.main()
