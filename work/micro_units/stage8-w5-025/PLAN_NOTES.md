# Plan Notes

## Scope
- `task` workflow planner의 후보 도구를 `internal.summary.generate`, `redmine.issue.create`, `slack.message.send`로 확장한다.
- task planner provenance에 `eligible_tools`를 기록해서 planner가 어떤 도구를 고려했는지 status/event에서 확인 가능하게 만든다.
- fallback planner와 live LLM planner 둘 다 ticket creation path를 다룰 수 있게 맞춘다.
- 기존 executor/report 루프는 유지하되, task path에서 `summary -> ticket -> slack` 순서의 3-step plan까지 허용한다.

## Out of Scope
- incident planner를 LLM planner로 전환하는 작업
- redmine issue update/comment/assign/transition을 task planner에 추가하는 작업
- task report 내용을 후속 action payload로 동적으로 참조하는 richer data binding
- operator UI 변경

## AI-First Planner Design
- 기본 경로는 계속 `LLM planner -> policy gate -> executor`다.
- planner는 tool registry allowlist를 기반으로 움직이고, task path의 eligible tool set은 runtime helper가 고정한다.
- `internal.summary.generate`는 항상 첫 action이어야 한다.
- `redmine.issue.create`는 ticket project id가 준비되고 follow-up/ticket intent가 감지될 때 후보군에 들어간다.
- `slack.message.send`는 notify channel이 있을 때만 후보군에 들어간다.
- live planner가 잘못된 plan을 반환하거나 비활성 상태면 deterministic fallback이 `summary -> ticket -> slack` 순서로 degraded mode plan을 만든다.

## Acceptance Criteria
- task planner contract test가 summary/ticket/slack eligibility와 fallback ordering을 검증한다.
- task runtime status에 `planning_provenance.eligible_tools`가 포함된다.
- ticket metadata가 있는 task 요청은 planner가 `redmine.issue.create`를 선택할 수 있다.
- QA runtime smoke에서 fallback 또는 mocked LLM plan 기준으로 `summary + ticket` 또는 `summary + ticket + slack` path가 통과한다.
- stage 8 micro-cycle과 QA canonical cycle이 통과한다.

## Risks
- ticket payload는 아직 summary 결과를 직접 참조하지 않으므로 description 품질이 raw input 중심일 수 있다.
- planner 후보군이 늘면서 fallback/LLM 응답 검증 로직이 더 엄격해져 기존 task tests와 충돌할 수 있다.
- redmine create가 task path에 들어오면 외부 실행 기대가 커지므로 eligibility 기준이 느슨하면 불필요한 action을 계획할 수 있다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage8-w5-025`
- `bash scripts/run_micro_cycle.sh gate-review stage8-w5-025`
- `python3 -m unittest tests.test_agent_planner_contract tests.test_agent_planner_runtime tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-025 8`
