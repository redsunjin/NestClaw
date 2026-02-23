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


def create_meeting_summary_task() -> None:
    global ACTOR_ID, ACTOR_ROLE
    print("\n[템플릿: 회의요약 -> 액션리스트]")
    meeting_title = _input_required("회의 제목")
    meeting_date = _input_required("회의 날짜 (YYYY-MM-DD)")
    participants_raw = _input_required("참석자 (쉼표로 구분)")
    notes = _input_required("회의 메모")
    requested_by = _input_required("요청자 ID")
    title = input("작업 제목 (기본: 회의요약 생성): ").strip() or "회의요약 생성"

    payload = {
        "title": title,
        "template_type": "meeting_summary",
        "input": {
            "meeting_title": meeting_title,
            "meeting_date": meeting_date,
            "participants": [x.strip() for x in participants_raw.split(",") if x.strip()],
            "notes": notes,
        },
        "requested_by": requested_by,
    }
    ACTOR_ID = requested_by
    ACTOR_ROLE = "requester"
    resp = _http_json(
        "POST",
        "/api/v1/task/create",
        payload,
        actor_id=ACTOR_ID,
        actor_role=ACTOR_ROLE,
    )
    if "error" in resp:
        _print_status(resp)
        return

    print("\n[생성 완료]")
    print(f"- Task ID: {resp.get('task_id')}")
    print(f"- 상태: {resp.get('status')}\n")


def run_task() -> None:
    global ACTOR_ID, ACTOR_ROLE
    task_id = _input_required("실행할 Task ID")
    idem = input("idempotency_key (선택): ").strip() or None
    payload = {"task_id": task_id, "idempotency_key": idem, "run_mode": "standard"}
    resp = _http_json("POST", "/api/v1/task/run", payload, actor_id=ACTOR_ID, actor_role=ACTOR_ROLE)
    _print_status(resp)


def show_status() -> None:
    global ACTOR_ID, ACTOR_ROLE
    task_id = _input_required("조회할 Task ID")
    resp = _http_json("GET", f"/api/v1/task/status/{task_id}", actor_id=ACTOR_ID, actor_role=ACTOR_ROLE)
    _print_status(resp)


def show_result() -> None:
    global ACTOR_ID, ACTOR_ROLE
    task_id = _input_required("결과 확인할 Task ID")
    resp = _http_json("GET", f"/api/v1/task/status/{task_id}", actor_id=ACTOR_ID, actor_role=ACTOR_ROLE)
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
        "1": ("회의요약 작업 생성", create_meeting_summary_task),
        "2": ("작업 실행", run_task),
        "3": ("상태 조회", show_status),
        "4": ("결과 확인", show_result),
        "5": ("종료", None),
    }

    print("Local Work Delegation CLI")
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
