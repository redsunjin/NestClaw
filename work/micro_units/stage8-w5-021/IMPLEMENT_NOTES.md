# Implement Notes

## Changed Files
- `app/services/approval_service.py`
  - approval detail payload와 action/comment history 조회를 추가한다.
- `app/main.py`
  - `GET /api/v1/approvals/{queue_id}` route를 추가한다.
- `app/static/agent-console.html`
  - approval detail/history panel을 추가한다.
- `app/static/agent-console.js`
  - approval queue/recent approval 카드의 `상세/이력` drill-down과 approve/reject 후 detail refresh를 추가한다.
- `app/static/agent-console.css`
  - approval history detail panel 스타일을 추가한다.
- `README.md`, `TASKS.md`, `NEXT_WORK_GROUPS_2026-03-13.md`, `API_CONTRACT.md`
  - operator surface와 next-work plan을 현재 상태에 맞게 갱신한다.
- `tests/test_runtime_smoke.py`, `tests/test_web_console_runtime.py`, `tests/test_stage8_contract.py`
  - approval detail auth/history와 UI wiring을 회귀 테스트로 고정한다.

## Rollback Plan
- `GET /api/v1/approvals/{queue_id}` route와 `ApprovalService.get_approval()`를 제거한다.
- Web Console의 approval detail/history panel과 `상세/이력` 버튼을 제거하고 기존 list/approve/reject 동선만 유지한다.
- 문서에서 approval drill-down 관련 항목을 제거한다.

## Known Risks
- approval detail은 approver/admin 전용이므로 requester role에서는 UI에서 403이 계속 보일 수 있다. 이는 정책 유지에 따른 의도된 동작이다.
- action history는 현재 text summary로만 보여주므로 comment formatting이 긴 경우 가독성이 떨어질 수 있다.
- approval resolved item detail은 감사 목적상 계속 조회되므로 action list가 커지면 후속 paging이 필요할 수 있다.
