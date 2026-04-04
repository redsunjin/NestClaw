# Plan Notes

## Scope
- `app/main.py`에 남아 있는 task/incident 공통 provider selection 기록 경로를 helper로 추출한다.
- report 파일 쓰기와 `result/completed_at/DONE` 최종 마감 로직을 공통 helper로 정리한다.
- incident의 `action_cards`는 하위 호환 필드로 유지하되, 저장 경로는 `planned_actions` 기반 rail에 더 가깝게 정리한다.
- stage9 contract와 helper unit test를 보강하고, task/incident runtime smoke가 회귀를 잡도록 유지한다.

## Out of Scope
- incident AI planner 도입
- action card/action result payload shape의 대규모 API 변경
- dashboard/quickstart UI 구조 변경
- live env, sandbox env, pilot readiness 재개

## AI-First Planner Design
- 이번 단위의 목적은 planner 자체를 더 AI-first로 만드는 것이 아니라, provider selection과 report/result finalization도 공통 runtime rail에 넣어 planner/executor/reporter 계약을 더 단단하게 만드는 것이다.
- task는 기존 LLM planner baseline을 유지하고, incident는 deterministic planner baseline을 유지한다.
- 공통 helper는 planner 종류와 무관하게 `selection -> actions -> results -> report -> done` 흐름의 후반부를 재사용 가능하게 만드는 데 집중한다.
- incident의 `action_cards`는 compatibility surface로 남기되, canonical contract는 여전히 `planned_actions`, `planning_provenance`, `action_results`, `result`다.

## Acceptance Criteria
- task와 incident가 공통 provider-selection recording helper를 사용한다.
- task와 incident가 공통 report write / result finalization helper를 사용한다.
- `app/main.py`에서 workflow별 report/result 마감 중복이 줄어든다.
- `tests.test_planner_executor_service`, `tests.test_stage9_contract`, `tests.test_agent_planner_runtime`, `tests.test_incident_runtime_smoke`가 통과한다.
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`가 통과한다.

## Risks
- `_set_status`와 helper 순서가 바뀌면 `completed_at`, `result`, `STATUS_CHANGED` event timing이 어긋날 수 있다.
- incident의 `action_cards` compatibility를 건드리면 기존 runtime/status 테스트가 깨질 수 있다.
- provider selection helper 추출 과정에서 persistence/event emission 순서가 바뀌면 audit 해석이 흐려질 수 있다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage9-w1-002`
- `bash scripts/run_micro_cycle.sh gate-review stage9-w1-002`
- `python3 -m unittest tests.test_stage9_contract tests.test_planner_executor_service`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_planner_executor_service tests.test_stage9_contract tests.test_agent_planner_runtime tests.test_incident_runtime_smoke`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_micro_cycle.sh run stage9-w1-002 9`
