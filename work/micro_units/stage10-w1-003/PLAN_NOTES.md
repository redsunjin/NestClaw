# Plan Notes

## Scope
- runtime과 readiness가 공통으로 쓰는 canonical state/reason taxonomy를 추가한다.
- `status`, `recent`, `bundle`, `capabilities`가 `blocked / approval_pending / retryable_failure / planner_degraded`를 같은 필드명으로 노출하게 맞춘다.
- quickstart와 console이 새 taxonomy를 읽어 operator에게 이유를 같은 vocabulary로 보여주게 다듬는다.
- 관련 runtime smoke, CLI/MCP smoke, stage10 contract를 보강하고 전체 stage10 cycle을 다시 실행한다.

## Out of Scope
- backend approval semantics 자체 변경
- Stage 8 external env 확보 또는 readiness bundle 절차 변경
- 새로운 workflow family 추가
- dashboard 내 chat panel 추가
- transport/auth hardening 자체 구현

## AI-First Planner Design
- 이번 단계는 planner를 더 똑똑하게 만드는 작업이 아니라, planner fallback/degraded 상태와 approval/retry 상태를 operator와 upper agent가 같은 어휘로 읽게 만드는 작업이다.
- task/incident는 계속 기존 planner/executor rail을 사용하되, payload 표면에서 `canonical_state`와 `canonical_reason_code`를 제공해야 한다.
- readiness도 같은 원칙을 따라 `env missing`을 runtime failure처럼 보이게 하면 안 되고, 명시적 `env_blocked`로 분리돼야 한다.
- 따라서 구현은 shared taxonomy helper를 만든 뒤 status/recent/bundle/capability manifest/UI 요약에 재사용하는 방식이 적절하다.

## Acceptance Criteria
- `/api/v1/capabilities`의 `stage8_live_readiness`가 canonical reason code를 포함한다.
- `/api/v1/agent/status/{task_id}`, `/api/v1/agent/bundle/{task_id}`, `/api/v1/agent/recent`가 `state_summary`를 포함한다.
- external send 승인 대기 task는 `policy_blocked`, retryable failure는 `retryable_failure`, planner fallback은 `planner_degraded`로 읽힌다.
- quickstart와 console이 새 canonical reason을 summary/signal 수준에서 노출한다.
- `tests.test_capability_manifest_runtime`, `tests.test_agent_entrypoint_smoke`, `tests.test_tool_cli_smoke`, `tests.test_mcp_server_smoke`, `tests.test_web_console_runtime`, `tests.test_stage10_contract`, `bash scripts/run_dev_qa_cycle.sh 10`이 통과한다.

## Risks
- canonical reason을 너무 세분화하면 surface 간 parity가 오히려 깨질 수 있다.
- readiness의 `blocked`와 runtime의 `approval_pending`을 혼동하면 operator copy가 다시 흐려질 수 있다.
- existing consumers가 `status`만 보던 곳에서 새 summary를 잘못 우선시하면 해석 차이가 생길 수 있다.
- JS summary가 길어지면 quickstart가 다시 복잡해질 수 있어 compact exposure가 필요하다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage10-w1-003`
- `bash scripts/run_micro_cycle.sh gate-review stage10-w1-003`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_capability_manifest_runtime tests.test_agent_entrypoint_smoke tests.test_tool_cli_smoke tests.test_mcp_server_smoke tests.test_web_console_runtime tests.test_stage10_contract`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 10`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_micro_cycle.sh run stage10-w1-003 10`
