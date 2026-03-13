# Plan Notes

## Scope
- Web Console에 승인 큐 조회와 approve/reject 액션을 추가한다.
- agent 제출 화면에 `승인필요 예시`를 넣어 approval surface를 바로 재현할 수 있게 한다.
- backend approval API 계약은 바꾸지 않고 static UI만 확장한다.

## Out of Scope
- approval 이력 전체 대시보드
- reviewer 전용 감사 화면
- 다중 작업 bulk approve/reject

## Acceptance Criteria
- Console에서 `/api/v1/approvals` 목록을 볼 수 있다.
- 카드에서 approve/reject를 바로 실행할 수 있다.
- 승인필요 예시를 제출하면 status와 approval 큐 흐름을 같은 화면에서 따라갈 수 있다.
- runtime smoke와 contract 검사가 approval surface를 포함한다.

## Risks
- approver role/acted_by 불일치 시 브라우저에서 403이 나므로 에러 메시지가 명확해야 한다.
- approval list를 auto-refresh하지 않으면 최신 상태가 늦게 보일 수 있다.
- UI 범위를 넓히면 console이 복잡해질 수 있으므로 이번에는 승인 큐 최소 기능만 둔다.

## Test Plan
- `python3 -m unittest tests.test_web_console_runtime tests.test_runtime_smoke tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh gate-plan stage8-w5-017`
- 구현 후 `bash scripts/run_micro_cycle.sh run stage8-w5-017 8`
