# Plan Notes

## Scope
- `task_kind=auto` 경로를 별도 intent classifier module로 분리한다.
- classifier는 model registry selection을 사용해 live LLM 시도를 하고, 실패/미설정 시 heuristic으로 안전하게 fallback 한다.
- agent task state/status/event에 intent classification 결과를 기록한다.
- classifier contract/runtime smoke와 Stage 8 게이트 연동을 추가한다.

## Out of Scope
- 실제 task/incident provider invocation 연결
- operator UI
- multi-step extraction of detailed metadata
- non-local LLM provider 구현 확대
- sandbox/live rehearsal

## Acceptance Criteria
- `task_kind=auto`가 direct heuristic 대신 classifier callback을 통해 resolved kind를 결정한다.
- classifier 결과에 `source`, `confidence`, `provider_selection`이 포함된다.
- task status와 event log에 intent classification 정보가 보인다.
- live classifier가 비활성/실패일 때 기존 heuristic으로 안전하게 fallback 한다.
- 관련 unit/runtime tests와 `bash scripts/run_micro_cycle.sh run stage8-w5-007 8`가 통과한다.

## Risks
- classifier 실패 시 fallback을 잘못 연결하면 기존 auto routing이 깨질 수 있다.
- live provider 호출이 느리거나 불안정하면 request latency가 늘 수 있다.
- classification 결과를 과하게 신뢰하면 incident/task 오분류가 늘 수 있다.

## Test Plan
- 정적:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
- 런타임:
  - `python3 -m unittest tests.test_intent_classifier_contract tests.test_intent_classifier_runtime tests.test_agent_entrypoint_smoke`
- 품질 게이트:
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-007 8`
