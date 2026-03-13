from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import sys
from typing import Any


def _close_connection(store: Any) -> None:
    conn = getattr(store, "conn", None)
    if conn is None:
        return
    close = getattr(conn, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass


def _sync_rebuilt_store(main_module: Any, new_store: Any) -> None:
    main_module.STATE_STORE = new_store

    orchestration_service = getattr(main_module, "ORCHESTRATION_SERVICE", None)
    if orchestration_service is not None and hasattr(orchestration_service, "deps"):
        setattr(orchestration_service.deps, "state_store", new_store)

    cli_module = sys.modules.get("app.cli")
    cli_service = getattr(cli_module, "CLI_ORCHESTRATION_SERVICE", None) if cli_module is not None else None
    if cli_service is not None and hasattr(cli_service, "deps"):
        setattr(cli_service.deps, "state_store", new_store)


def _rebuild_sqlite_store(main_module: Any, db_path: Path) -> Any:
    _close_connection(getattr(main_module, "STATE_STORE", None))
    if db_path.is_file():
        db_path.unlink()
    new_store = main_module.create_state_store()
    _sync_rebuilt_store(main_module, new_store)
    return new_store


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

        db_path = Path(getattr(store, "db_path", os.getenv("NEWCLAW_DB_PATH", "")) or "")
        if db_path and str(db_path).startswith("/tmp/"):
            store = _rebuild_sqlite_store(main_module, db_path)
            conn = getattr(store, "conn", None)
            if conn is None:
                return

        table_names = ("approval_actions", "approvals", "events", "run_idempotency", "tasks")
        try:
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
        except sqlite3.DatabaseError as exc:
            message = str(exc).lower()
            if "malformed" not in message and "not a database" not in message:
                raise
            if not db_path:
                raise
            rebuilt_store = _rebuild_sqlite_store(main_module, db_path)
            rebuilt_conn = getattr(rebuilt_store, "conn", None)
            if rebuilt_conn is None:
                raise
            if hasattr(rebuilt_conn, "commit"):
                rebuilt_conn.commit()

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
