# Plan Notes

## Scope
- 실행 도구를 설명하는 `tool registry / capability schema`를 새 설정 파일과 로더 모듈로 추가한다.
- 현재 incident action-card가 하드코딩한 Redmine create 동작을 registry 기반 정의로 치환한다.
- tool catalog 조회 표면을 API / CLI / MCP에 추가해 사람이든 에이전트든 현재 사용 가능한 도구를 확인할 수 있게 한다.
- 회귀 방지용 계약/스모크 테스트를 추가한다.

## Out of Scope
- 새로운 외부 도구 실제 연동 추가
- planner가 다중 도구를 자동 선택하는 범용 계획기 구현
- operator UI
- live sandbox rehearsal / provider invocation 확장

## Acceptance Criteria
- `configs/tool_registry.yaml`과 runtime loader가 추가되고 최소 1개 이상의 execution tool이 registry에 정의된다.
- incident action-card 생성 시 registry 기반 capability metadata를 사용한다.
- API / CLI / MCP에서 tool catalog를 조회할 수 있다.
- `python3 -m unittest` 기반 계약/스모크 테스트와 `bash scripts/run_micro_cycle.sh run stage8-w5-010 8`가 통과한다.

## Risks
- registry 스키마를 너무 크게 잡으면 현재 하드코딩 경로를 옮기는 작업이 과해질 수 있다.
- incident policy 테스트가 기존 action-card 모양에 의존하고 있어 필드명을 잘못 바꾸면 회귀가 생길 수 있다.
- MCP에 catalog tool을 추가할 때 protocol-level `tools/list`와 business-level catalog tool 명칭이 혼동될 수 있다.

## Test Plan
- 정적/런타임:
  - `python3 -m unittest tests.test_tool_registry_contract tests.test_tool_cli_smoke tests.test_mcp_server_smoke tests.test_incident_runtime_smoke tests.test_stage8_contract`
- 품질 게이트:
  - `bash scripts/run_micro_cycle.sh run stage8-w5-010 8`
