from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib import error, request


BASE_URL = "http://127.0.0.1:8000"
ACTOR_ID = "user_cli"
ACTOR_ROLE = "requester"


def _http_json(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    actor_id: str | None = None,
    actor_role: str | None = None,
) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    data = None
    headers = {"Content-Type": "application/json"}
    if actor_id:
        headers["X-Actor-Id"] = actor_id
    if actor_role:
        headers["X-Actor-Role"] = actor_role
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = request.Request(url, method=method, headers=headers, data=data)
    try:
        with request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        try:
            parsed = json.loads(detail)
        except Exception:
            parsed = {"error": {"code": "HTTP_ERROR", "message": detail or str(exc)}}
        return parsed
    except Exception as exc:
        return {"error": {"code": "NETWORK_ERROR", "message": str(exc)}}


def _input_required(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("필수 입력입니다.")


def _print_status(payload: dict[str, Any]) -> None:
    # Standardized status message for non-IT users.
    print("\n[상태 보고]")
    print(f"- Task ID: {payload.get('task_id', '-')}")
    if payload.get("resolved_kind"):
        print(f"- 처리 종류: {payload.get('resolved_kind')}")
    print(f"- 현재 상태: {payload.get('status', '-')}")
    print(f"- 다음 액션: {payload.get('next_action', '-')}")
    if payload.get("status") == "NEEDS_HUMAN_APPROVAL":
        print(f"- 승인 필요 사유: {payload.get('approval_reason', '-')}")
        print(f"- 승인 큐 ID: {payload.get('approval_queue_id', '-')}")
    if payload.get("status") == "DONE":
        result = payload.get("result") or {}
        report_path = result.get("report_path")
        if report_path:
            print(f"- 결과 파일: {report_path}")
    if "error" in payload:
        err = payload["error"]
        print(f"- 오류: {err.get('code')}: {err.get('message')}")
    print()


def submit_agent_request() -> None:
    global ACTOR_ID, ACTOR_ROLE
    print("\n[Agent Submit]")
    task_kind = input("요청 유형 (auto/task/incident, 기본: auto): ").strip().lower() or "auto"
    title = input("작업 제목 (선택): ").strip() or None
    request_text = _input_required("요청 내용")
    requested_by = _input_required("요청자 ID")
    metadata: dict[str, Any] = {}
    run_mode = "dry-run"

    if task_kind in {"task", "meeting", "meeting_summary"}:
        metadata["meeting_title"] = input("회의 제목 (선택): ").strip() or title or "Agent Request"
        metadata["meeting_date"] = input("회의 날짜 (YYYY-MM-DD, 기본: 오늘): ").strip()
        participants_raw = input("참석자 (쉼표 구분, 기본: 요청자): ").strip()
        metadata["participants"] = [x.strip() for x in participants_raw.split(",") if x.strip()] if participants_raw else [requested_by]
        metadata["notes"] = input("회의 메모 (비우면 요청 내용 사용): ").strip() or request_text
        task_kind = "task"
    elif task_kind == "incident":
        metadata["service"] = _input_required("서비스명")
        metadata["severity"] = input("심각도 (low/medium/high/critical, 기본: low): ").strip().lower() or "low"
        metadata["source"] = input("감지 출처 (기본: agent): ").strip() or "agent"
        metadata["time_window"] = input("시간 구간 (기본: 15m): ").strip() or "15m"
        metadata["policy_profile"] = input("정책 프로필 (기본: default): ").strip() or "default"
        run_mode = input("incident run_mode (dry-run/mcp-live/live, 기본: dry-run): ").strip().lower() or "dry-run"

    payload = {
        "title": title,
        "task_kind": task_kind,
        "request_text": request_text,
        "metadata": metadata,
        "requested_by": requested_by,
        "auto_run": True,
        "incident_run_mode": run_mode,
    }
    ACTOR_ID = requested_by
    ACTOR_ROLE = "requester"
    resp = _http_json(
        "POST",
        "/api/v1/agent/submit",
        payload,
        actor_id=ACTOR_ID,
        actor_role=ACTOR_ROLE,
    )
    _print_status(resp)


def show_status() -> None:
    global ACTOR_ID, ACTOR_ROLE
    task_id = _input_required("조회할 Task ID")
    resp = _http_json("GET", f"/api/v1/agent/status/{task_id}", actor_id=ACTOR_ID, actor_role=ACTOR_ROLE)
    _print_status(resp)


def show_events() -> None:
    global ACTOR_ID, ACTOR_ROLE
    task_id = _input_required("이벤트 조회할 Task ID")
    resp = _http_json("GET", f"/api/v1/agent/events/{task_id}", actor_id=ACTOR_ID, actor_role=ACTOR_ROLE)
    if "error" in resp:
        _print_status(resp)
        return
    print("\n[이벤트]")
    for item in resp.get("items", [])[-10:]:
        print(f"- {item.get('created_at', '-')}: {item.get('event_type', '-')}")
    print()


def show_result() -> None:
    global ACTOR_ID, ACTOR_ROLE
    task_id = _input_required("결과 확인할 Task ID")
    resp = _http_json("GET", f"/api/v1/agent/status/{task_id}", actor_id=ACTOR_ID, actor_role=ACTOR_ROLE)
    _print_status(resp)
    if resp.get("status") != "DONE":
        return
    result = resp.get("result") or {}
    report_path = result.get("report_path")
    if not report_path:
        return
    path = Path(report_path)
    if not path.exists():
        print("결과 파일이 아직 로컬에 없습니다.\n")
        return
    print("[결과 미리보기]")
    preview = path.read_text(encoding="utf-8").splitlines()[:20]
    for line in preview:
        print(line)
    print()


def main() -> int:
    global ACTOR_ID, ACTOR_ROLE
    actor_id_input = input("작업자 ID (기본: user_cli): ").strip()
    if actor_id_input:
        ACTOR_ID = actor_id_input
    actor_role_input = input("작업자 Role (requester/reviewer/approver/admin, 기본: requester): ").strip().lower()
    if actor_role_input in {"requester", "reviewer", "approver", "admin"}:
        ACTOR_ROLE = actor_role_input

    menu = {
        "1": ("Agent 요청 제출", submit_agent_request),
        "2": ("상태 조회", show_status),
        "3": ("이벤트 조회", show_events),
        "4": ("결과 확인", show_result),
        "5": ("종료", None),
    }

    print("NewClaw Agent CLI")
    print(f"- API: {BASE_URL}\n")
    print(f"- Actor ID: {ACTOR_ID}")
    print(f"- Actor Role: {ACTOR_ROLE}\n")

    while True:
        print("메뉴:")
        for key, (label, _) in menu.items():
            print(f"{key}. {label}")
        choice = input("선택: ").strip()
        if choice == "5":
            print("종료합니다.")
            return 0
        action = menu.get(choice, (None, None))[1]
        if action is None:
            print("올바른 번호를 선택하세요.\n")
            continue
        action()


if __name__ == "__main__":
    sys.exit(main())
