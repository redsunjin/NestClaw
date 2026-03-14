#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-status}"

python3 - "$MODE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from app.tool_registry import (
    DEFAULT_TOOL_REGISTRY_OVERLAY_PATH,
    compact_overlay_tool_registry,
    load_overlay_tool_registry,
    validate_tool_capability,
)


mode = sys.argv[1]
overlay_path = Path(DEFAULT_TOOL_REGISTRY_OVERLAY_PATH)
drafts_root = Path("work/tool_drafts")
history_root = Path("work/tool_registry_history")


def status() -> int:
    overlay = load_overlay_tool_registry(overlay_path)
    payload = {
        "overlay_path": str(overlay_path),
        "overlay_exists": overlay is not None,
        "overlay_tool_count": len(overlay.tools) if overlay is not None else 0,
        "draft_count": len(list(drafts_root.glob("*.yaml"))) if drafts_root.is_dir() else 0,
        "history_count": len(list(history_root.glob("*.json"))) if history_root.is_dir() else 0,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def validate() -> int:
    overlay = load_overlay_tool_registry(overlay_path)
    if overlay is None:
        print(json.dumps({"overlay_exists": False, "valid": True, "checks": []}, ensure_ascii=False, indent=2))
        return 0
    reports = [validate_tool_capability(item.as_dict()) for item in overlay.tools]
    payload = {
        "overlay_exists": True,
        "valid": all(item["valid"] for item in reports),
        "checks": reports,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["valid"] else 1


def compact() -> int:
    payload = compact_overlay_tool_registry(overlay_path=overlay_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


handlers = {
    "status": status,
    "validate": validate,
    "compact": compact,
}

if mode not in handlers:
    print(json.dumps({"error": f"unsupported mode: {mode}"}, ensure_ascii=False, indent=2))
    raise SystemExit(2)

raise SystemExit(handlers[mode]())
PY
