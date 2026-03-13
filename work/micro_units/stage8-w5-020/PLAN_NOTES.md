# Plan Notes

## Scope
- `agent report preview` API를 추가해 task/incident 결과 보고서를 권한 검사 후 읽을 수 있게 만든다.
- `agent report raw` API를 추가해 현재 actor 권한으로 markdown 원문을 열 수 있게 만든다.
- Web Console recent task 카드와 실행 상태 패널에서 report preview / raw open 동선을 제공한다.
- G1 grouped plan 문서와 README/TASKS/API 문서를 현재 상태에 맞게 갱신한다.

## Out of Scope
- report markdown 렌더러 추가
- approval history 상세 drill-down
- auto-refresh/polling UX

## Acceptance Criteria
- `/api/v1/agent/report/{task_id}`가 동작하고 requester 접근 제한을 유지한다.
- `/api/v1/agent/report/{task_id}/raw`가 동작한다.
- Web Console에서 최근 task 카드로 report 미리보기와 원문 열기를 실행할 수 있다.
- 현재 task 상태 패널에서도 report 미리보기/원문 열기를 할 수 있다.

## Risks
- report path를 그대로 열면 path traversal 또는 잘못된 파일 노출 위험이 있다.
- raw report 열기는 현재 Web Console의 header 기반 auth를 유지해야 하므로 anchor 직링크가 아니라 fetch/blob 방식이 필요하다.
- large report를 전부 preview하면 UI가 무거워질 수 있다.

## Test Plan
- `python3 -m unittest tests.test_web_console_runtime tests.test_agent_entrypoint_smoke tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-020 8`
- QA worktree에서 canonical cycle과 실제 서버 `/` + report preview/raw 확인
