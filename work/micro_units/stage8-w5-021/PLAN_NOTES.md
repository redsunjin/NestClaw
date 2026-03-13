# Plan Notes

## Scope
- `GET /api/v1/approvals/{queue_id}` detail API를 추가해 승인 항목과 action/comment history를 조회 가능하게 만든다.
- Web Console에서 approval queue 카드와 recent approval 카드 모두 detail/history drill-down을 열 수 있게 만든다.
- 승인 처리 후 같은 화면에서 최신 comment/history를 다시 볼 수 있게 연결한다.
- README/TASKS/API_CONTRACT/NEXT_WORK_GROUPS를 현재 operator surface 상태에 맞게 갱신한다.

## Out of Scope
- approval auto-refresh/polling
- approval comment edit/delete
- requester에게 approval detail 노출

## Acceptance Criteria
- approver/admin이 approval detail과 action/comment history를 조회할 수 있다.
- requester는 approval detail을 조회할 수 없다.
- Web Console에서 `상세/이력` 버튼으로 approval detail panel을 채울 수 있다.
- approve/reject 후 detail panel에 최신 상태와 comment가 반영된다.

## Risks
- approval detail이 comment를 그대로 노출하므로 role 경계가 느슨해지면 안 된다.
- action history 정렬이 뒤바뀌면 operator가 흐름을 잘못 읽을 수 있다.
- queue 카드와 recent 카드 두 군데에서 같은 핸들러를 재사용하지 않으면 UI가 쉽게 어긋날 수 있다.

## Test Plan
- `python3 -m unittest tests.test_web_console_runtime tests.test_runtime_smoke tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-021 8`
- QA worktree에서 canonical cycle과 실제 서버 approval detail/history 확인
