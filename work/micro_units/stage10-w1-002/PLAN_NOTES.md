# Plan Notes

## Scope
- `/console`과 quickstart에서 requester/reviewer와 approver/admin의 제어면을 시각적으로 분리한다.
- approval queue, approval detail/history, apply-like governance control, live run option을 role 기준으로 숨기거나 비활성화한다.
- requester가 보게 될 empty state / helper copy를 `읽기 중심`으로 바꾸고, approver/admin에게만 운영 제어 copy를 노출한다.
- 관련 UI runtime test를 보강하고 stage10 cycle 기준으로 회귀를 다시 실행한다.

## Out of Scope
- backend RBAC/policy semantics 변경
- 새로운 승인/감사 API 추가
- dashboard 안 chat panel 추가
- tool draft authoring permission 자체 변경
- Stage 8 readiness env 확보 또는 운영 절차 변경

## AI-First Planner Design
- 이번 단계는 planner intelligence를 바꾸는 작업이 아니라, planner/execution 결과를 읽는 dashboard의 `role-aware operator experience`를 다듬는 작업이다.
- requester는 planner summary와 report/approval summary를 읽고, approver/admin만 approval detail과 high-risk control을 다루게 하는 것이 목표다.
- 따라서 UI는 기존 runtime contract를 그대로 읽고, role에 따라 `보여주는 깊이`와 `조작 가능성`만 달라져야 한다.
- task/incident planner source, rationale, action rail은 role과 무관하게 읽을 수 있어야 하고, governance control만 뒤로 물러나야 한다.

## Acceptance Criteria
- quickstart에서 requester/reviewer는 approval action 버튼과 acted-by 입력 없이 읽기 중심 상태만 본다.
- console에서 requester/reviewer는 approval queue/history/detail과 apply-like governance control을 직접 보지 않거나 조작하지 못한다.
- console에서 approver/admin은 기존 approval/detail/apply control을 계속 사용할 수 있다.
- non-elevated role에서는 live/mcp-live run option이 시각적으로 gated 된다.
- `tests.test_web_console_runtime`, `tests.test_agent_entrypoint_smoke`, `tests.test_stage10_contract`와 stage10 QA cycle이 통과한다.

## Risks
- 지나치게 많이 숨기면 현재 documented capability와 UI가 어긋날 수 있다.
- role gating을 DOM visibility에만 의존하면 클릭 경로나 JS 함수 호출로 빈번한 오류가 남을 수 있어, handler guard도 같이 필요하다.
- requester empty state를 과도하게 단순화하면 planner provenance나 report reading 같은 핵심 operator signal까지 약해질 수 있다.
- run mode gating을 UI에서만 처리하므로, backend policy와 표현이 어긋나지 않게 문구를 신중히 맞춰야 한다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage10-w1-002`
- `bash scripts/run_micro_cycle.sh gate-review stage10-w1-002`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_web_console_runtime tests.test_stage10_contract`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_agent_entrypoint_smoke tests.test_tool_cli_smoke`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 10`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_micro_cycle.sh run stage10-w1-002 10`
