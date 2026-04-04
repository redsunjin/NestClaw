# Plan Notes

## Scope
- `app/main.py`에 남아 있는 task/incident별 planner action materialization과 executor dispatch 중복을 공통 helper로 추출한다.
- task의 LLM planner 결과와 incident의 deterministic planner 결과가 같은 action descriptor -> execution call 변환 경로를 쓰게 정렬한다.
- prior-result binding, request payload normalization, action result shape를 workflow 간 공통 contract로 맞춘다.
- stage9 contract test를 추가하고 task/incident runtime smoke가 공통 loop 회귀를 잡도록 보강한다.

## Out of Scope
- incident workflow를 LLM planner로 전환하는 작업
- provider-backed incident reasoning/RAG 확장
- quickstart/console UI 변경
- live sandbox/pilot 실행 또는 운영 credential 확보

## AI-First Planner Design
- 이번 단위의 목적은 planner를 더 똑똑하게 만드는 것이 아니라, AI planner와 deterministic planner가 모두 꽂힐 수 있는 공통 executor rail을 고정하는 것이다.
- task는 기존 LLM planner baseline을 유지하고, incident는 기존 deterministic planner baseline을 유지하되 둘 다 같은 action materialization contract를 사용한다.
- 공통 executor는 `planned_actions`, `planning_provenance`, `action_results`를 workflow 공통 필드로 남겨 후속 UI와 audit surface가 workflow별 분기를 줄이게 만든다.
- binding은 planner 추론이 아니라 deterministic post-processing 계층으로 유지하고, prior action 결과를 다음 action payload에 주입하는 규칙은 공통 helper에서만 관리한다.

## Acceptance Criteria
- task와 incident가 공통 planner/executor helper를 사용하도록 `app/main.py` 밖의 재사용 가능한 모듈 또는 service helper가 추가된다.
- task와 incident의 `action_results`가 최소 공통 필드(`action_id`, `tool_id`, `adapter`, `method`, `mode`, `request_payload`)를 일관되게 남긴다.
- execution binding helper가 workflow 공통 경로가 되며, incident에서도 같은 interface로 prior-result binding을 적용하거나 no-op 처리할 수 있다.
- `tests.test_stage9_contract`, `tests.test_agent_planner_runtime`, `tests.test_incident_runtime_smoke`가 통과한다.
- `bash scripts/run_dev_qa_cycle.sh 9`가 통과한다.

## Risks
- planner/executor 추출 과정에서 event emission 순서가 바뀌면 기존 runtime smoke와 operator surface가 회귀할 수 있다.
- incident action에만 있는 `evidence_links`, `mcp_call` 같은 필드가 공통 schema 정리 과정에서 누락될 수 있다.
- binding helper를 공통화하면서 task 전용 summary output 전제가 incident payload에 잘못 적용되면 payload 오염이 생길 수 있다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage9-w1-001`
- `bash scripts/run_micro_cycle.sh gate-review stage9-w1-001`
- `python3 -m unittest tests.test_stage8_contract tests.test_stage9_contract`
- `python3 -m unittest tests.test_agent_planner_runtime tests.test_incident_runtime_smoke`
- `bash scripts/run_dev_qa_cycle.sh 9`
- `bash scripts/run_micro_cycle.sh run stage9-w1-001 9`
