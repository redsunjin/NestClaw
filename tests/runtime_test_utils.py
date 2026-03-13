from __future__ import annotations

from pathlib import Path
from typing import Any


def reset_runtime_state(main_module: Any) -> None:
    with main_module.STORE_LOCK:
        main_module.TASKS.clear()
        main_module.TASK_EVENTS.clear()
        main_module.APPROVAL_QUEUE.clear()
        main_module.APPROVAL_ACTIONS.clear()
        main_module.RUN_IDEMPOTENCY.clear()

        store = main_module.STATE_STORE
        conn = getattr(store, "conn", None)
        if conn is None:
            return

        table_names = ("approval_actions", "approvals", "events", "run_idempotency", "tasks")
        if hasattr(conn, "cursor"):
            cur = conn.cursor()
            try:
                for table_name in table_names:
                    cur.execute(f"DELETE FROM {table_name}")
            finally:
                close = getattr(cur, "close", None)
                if callable(close):
                    close()
        else:
            for table_name in table_names:
                conn.execute(f"DELETE FROM {table_name}")

        if hasattr(conn, "commit"):
            conn.commit()

    overlay_path = getattr(main_module, "TOOL_REGISTRY_OVERLAY_PATH", None)
    if overlay_path is not None:
        target = Path(overlay_path)
        if target.is_file():
            target.unlink()

    drafts_root = getattr(main_module, "TOOL_DRAFTS_ROOT", None)
    if drafts_root is not None:
        root = Path(drafts_root)
        if root.is_dir():
            for draft_file in root.glob("tooldraft_*.yaml"):
                draft_file.unlink()

    reload_registry = getattr(main_module, "_reload_tool_registry_runtime", None)
    if callable(reload_registry):
        reload_registry()
