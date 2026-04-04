# Plan Notes

## Scope
- incident planner를 `deterministic baseline only`에서 `LLM baseline + deterministic fallback` 구조로 확장한다.
- `app/agent_planner.py`에 incident planner prompt, action normalization, fallback decision을 추가한다.
- `app/main.py`의 incident planned action 생성 경로를 planner decision 기반으로 바꾸고, planner rationale/fallback_reason/provider_selection을 provenance와 payload에 반영한다.
- model registry에 incident planner routing rule을 추가하고, contract/runtime smoke로 경로를 검증한다.

## Out of Scope
- incident live RAG 도입
- 새로운 incident tool family 추가
- approval policy semantics 변경
- dashboard/quickstart UI 변경
- Stage 8 external sandbox/live readiness 재개

## AI-First Planner Design
- incident workflow도 task와 같은 `planner decision -> planned_actions -> planning_provenance` rail을 사용하되, incident 특성상 deterministic fallback을 더 강하게 유지한다.
- LLM planner가 활성화되고 응답이 유효하면 `planning_provenance.source=llm`, 실패/비활성 시에는 deterministic fallback source로 내려간다.
- planner provider selection은 `planning_provenance.provider_selection`에 기록하고, workflow-level provider selection(`incident_response`)과 구분해 관찰 가능하게 유지한다.
- incident payload에는 planner rationale을 반영해 operator가 “왜 이 action 조합이 선택됐는지”를 ticket/report 수준에서도 읽을 수 있게 한다.

## Acceptance Criteria
- incident workflow가 AI planner enabled 환경에서 `llm` source planning_provenance를 남길 수 있다.
- incident workflow가 planner disabled 또는 planner error 환경에서 deterministic fallback으로 완료된다.
- incident planning provenance가 `provider_selection`, `fallback_reason`, `degraded_mode`를 일관되게 기록한다.
- notify channel이 있는 dry-run incident는 2개 이상 action을 계획할 수 있다.
- `tests.test_agent_planner_contract`, `tests.test_incident_runtime_smoke`, `tests.test_model_registry_contract`, `tests.test_stage9_contract`가 통과한다.
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`가 통과한다.

## Risks
- incident planner가 잘못된 tool 순서를 내면 approval gate나 runtime dispatch보다 앞에서 깨질 수 있다.
- planning provenance의 source/fallback semantics가 바뀌면 기존 smoke와 operator 해석이 어긋날 수 있다.
- model registry routing rule 추가가 다른 task_type selection을 의도치 않게 가리면 Stage 8 runtime smoke가 흔들릴 수 있다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage9-w1-003`
- `bash scripts/run_micro_cycle.sh gate-review stage9-w1-003`
- `python3 -m unittest tests.test_agent_planner_contract tests.test_model_registry_contract tests.test_stage9_contract`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_agent_planner_contract tests.test_model_registry_contract tests.test_incident_runtime_smoke tests.test_model_registry_runtime`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_micro_cycle.sh run stage9-w1-003 9`
