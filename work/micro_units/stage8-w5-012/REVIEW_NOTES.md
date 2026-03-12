# Review Notes

## Security / Policy Review
- 공통 executor가 생겨도 `BLOCKED_POLICY`, `NEEDS_HUMAN_APPROVAL`, approval queue semantics는 workflow별로 약화되면 안 된다.
- internal provider invocation도 외부/민감 전송 가능성이 있으면 동일한 policy block을 먼저 거쳐야 한다.
- tool registry에 internal action을 넣더라도 allowlist 성격은 유지하고, 임의 함수 호출 테이블로 흐르지 않게 해야 한다.

## Architecture / Workflow Review
- 현재 구조의 핵심 문제는 `_execute_once`와 `_execute_incident_once`가 planner/executor/reporter를 각자 직접 들고 있다는 점이다.
- 공통화 기준 계약은 `planned_action` 하나로 잡는 것이 맞다. 현재 incident action-card를 확장해 task summary도 같은 계약으로 올리는 방향이 가장 자연스럽다.
- 제안 구조:
  - `plan_task_actions(task) -> [planned_action]`
  - `plan_incident_actions(task) -> [planned_action]`
  - `execute_planned_actions(task, actions) -> results`
  - adapter registry는 `provider_invoker`, `redmine_mcp` 등으로 통일
- task/incident의 차이는 planner 이전 컨텍스트 수집 단계에 남기고, planner 이후는 최대한 공통 루프로 모아야 한다.

## QA Gate Review
- 다음 구현 단위에서 필수 검증:
  - task summary가 `internal.summary.generate` 같은 internal capability를 통해 실행되는지
  - incident action-card가 같은 executor dispatch를 타는지
  - approval/policy regression이 없는지
- 이번 review 단계에서는 `tests.test_stage8_contract` 통과와 notes 완결성을 기준으로 한다.

## Review Verdict
- 승인 (Approved as Next Refactor Blueprint)
- 핵심 판단:
  1. summary generation도 planner/executor 공통화를 위해 internal tool action으로 올리는 것이 맞다
  2. 공통화 1차 범위는 `planner 이후`, 즉 action planning / gate / adapter dispatch까지만 잡는 것이 적절하다
  3. RAG/live/provider 확장은 그 다음 단계로 미룬다
