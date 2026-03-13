# Plan Notes

## Scope
- `agent recent` API를 추가해 최근 task 히스토리를 조회 가능하게 만든다.
- Web Console에 최근 task / 최근 approval 히스토리 패널을 추가한다.
- 다음 작업을 그룹 단위로 묶은 계획 문서를 추가한다.

## Out of Scope
- approval backend 계약 변경
- 최근 task 상세 report 렌더링
- planner/tool execution 자체 고도화

## Acceptance Criteria
- `/api/v1/agent/recent`가 동작한다.
- Web Console에서 최근 task와 최근 approval을 각각 볼 수 있다.
- 최근 task 카드에서 status/events 조회로 이어질 수 있다.
- 다음 작업 그룹 계획 문서가 저장소 기준 문서로 추가된다.

## Risks
- recent API 권한 범위를 잘못 잡으면 requester가 다른 사용자의 task를 볼 수 있다.
- approval history는 기존 API 재사용이라 requester role에서는 403이 발생할 수 있다.
- 화면 카드가 늘어나면서 mobile 레이아웃이 깨질 수 있다.

## Test Plan
- `python3 -m unittest tests.test_web_console_runtime tests.test_agent_entrypoint_smoke tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-019 8`
- QA worktree에서 canonical cycle과 실제 서버 UI 확인
