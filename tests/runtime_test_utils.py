from __future__ import annotations

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
