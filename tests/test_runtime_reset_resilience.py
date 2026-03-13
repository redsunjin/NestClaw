from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import tempfile
from threading import Lock
from types import SimpleNamespace
import unittest

from app.persistence import create_state_store
from tests.runtime_test_utils import reset_runtime_state


class TestRuntimeResetResilience(unittest.TestCase):
    def test_reset_rebuilds_malformed_temp_sqlite_store(self) -> None:
        previous_path = os.environ.get("NEWCLAW_DB_PATH")
        with tempfile.TemporaryDirectory(prefix="newclaw-reset-") as tmp_dir:
            db_path = Path(tmp_dir) / "state.db"
            os.environ["NEWCLAW_DB_PATH"] = str(db_path)

            store = create_state_store()
            store.conn.close()
            db_path.write_bytes(b"this is not a sqlite database")
            store.conn = sqlite3.connect(str(db_path), check_same_thread=False)

            fake_module = SimpleNamespace(
                STORE_LOCK=Lock(),
                TASKS={"task_a": {"task_id": "task_a"}},
                TASK_EVENTS=[{"event_id": "evt_a"}],
                APPROVAL_QUEUE={"aq_a": {"queue_id": "aq_a"}},
                APPROVAL_ACTIONS=[{"action_id": "aa_a"}],
                RUN_IDEMPOTENCY={("task_a", "run"): "task_a"},
                STATE_STORE=store,
                create_state_store=create_state_store,
                ORCHESTRATION_SERVICE=SimpleNamespace(deps=SimpleNamespace(state_store=store)),
                TOOL_REGISTRY_OVERLAY_PATH=Path(tmp_dir) / "tool_registry_runtime.yaml",
                TOOL_DRAFTS_ROOT=Path(tmp_dir) / "tool_drafts",
            )

            reset_runtime_state(fake_module)

            self.assertEqual(fake_module.TASKS, {})
            self.assertEqual(fake_module.TASK_EVENTS, [])
            self.assertEqual(fake_module.APPROVAL_QUEUE, {})
            self.assertEqual(fake_module.APPROVAL_ACTIONS, [])
            self.assertEqual(fake_module.RUN_IDEMPOTENCY, {})
            self.assertIs(fake_module.ORCHESTRATION_SERVICE.deps.state_store, fake_module.STATE_STORE)
            conn = fake_module.STATE_STORE.conn
            rows = list(conn.execute("SELECT name FROM sqlite_master WHERE type='table'"))
            self.assertTrue(rows)

        if previous_path is None:
            os.environ.pop("NEWCLAW_DB_PATH", None)
        else:
            os.environ["NEWCLAW_DB_PATH"] = previous_path


if __name__ == "__main__":
    unittest.main()
