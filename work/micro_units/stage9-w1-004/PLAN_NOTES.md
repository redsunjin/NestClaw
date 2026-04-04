# Plan Notes

## Scope
- quickstart와 operator dashboard에서 planner rationale, fallback/degraded 상태, action sequence, execution detail을 바로 읽을 수 있게 노출한다.
- 기존 status payload를 재사용하되, 필요한 경우 recent item/summary rendering을 보강한다.
- incident planner rationale과 fallback reason이 task와 같은 surface 문법으로 보이도록 통일한다.
- web console runtime test와 stage9 contract를 보강하고 full stage9 QA cycle까지 다시 돌린다.

## Out of Scope
- 새로운 workflow family 추가
- approval policy semantics 변경
- CLI/MCP surface 확장
- dashboard 내 chat panel 추가
- live env / sandbox env unblock 작업

## AI-First Planner Design
- operator surface는 planner를 다시 실행하는 곳이 아니라, 이미 기록된 `planning_provenance`, `planned_actions`, `action_results`를 해석하는 곳이어야 한다.
- task와 incident 모두 같은 `source / degraded_mode / fallback_reason / rationale / planned_tools / executed_tools` 관찰 어휘를 사용한다.
- UI는 planner 자체보다 provenance와 execution rail을 더 선명하게 보여야 하며, operator가 “왜 이렇게 됐는지”를 빠르게 읽게 만드는 데 집중한다.

## Acceptance Criteria
- `/console`에서 planner rationale, fallback 상태, action sequence, execution 결과를 별도 요약면으로 볼 수 있다.
- `/` quickstart에서도 현재 task의 planner 상태와 action 흐름을 과도한 클릭 없이 읽을 수 있다.
- incident llm/fallback 상태가 task와 같은 surface vocabulary로 보인다.
- `tests.test_web_console_runtime`, `tests.test_stage9_contract`가 통과한다.
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`가 통과한다.

## Risks
- UI가 planner/debug 정보를 너무 많이 드러내면 operator가 읽기 어려운 정보 과밀 상태로 다시 갈 수 있다.
- quickstart와 console이 같은 payload를 다르게 해석하면 surface vocabulary가 갈라질 수 있다.
- role-gated 영역 안팎에 execution detail을 배치할 때 requester/approver 시각적 경계가 흐려질 수 있다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage9-w1-004`
- `bash scripts/run_micro_cycle.sh gate-review stage9-w1-004`
- `python3 -m unittest tests.test_web_console_runtime tests.test_stage9_contract`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_web_console_runtime tests.test_capability_manifest_runtime tests.test_incident_runtime_smoke`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_micro_cycle.sh run stage9-w1-004 9`
