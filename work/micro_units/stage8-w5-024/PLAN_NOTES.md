# Plan Notes

## Scope
- `task` workflow의 planner를 `LLM-first` 경로로 승격한다.
- LLM planner는 tool registry를 읽고 task 요청에 대해 `internal.summary.generate`와 `slack.message.send` 중 필요한 action plan을 생성한다.
- planner 결과를 `planning_provenance`와 이벤트 로그로 남긴다.
- LLM planner 실패/비활성 시 기존 deterministic planner를 `degraded mode` fallback으로 사용한다.
- 기존 executor/approval/report 루프는 유지하고 planner 출력 계약만 여기에 맞춘다.

## Out of Scope
- incident planner를 LLM planner로 교체하는 작업
- live RAG 확장
- operator UI 변경
- Redmine task planning 추가

## AI-First Planner Design
- 기본 경로는 `LLM planner -> policy gate -> existing executor`다.
- planner provider는 model registry에서 `task_type=plan_actions` 기준으로 선택한다.
- task planner의 초기 허용 도구는 `internal.summary.generate`와 `slack.message.send`로 제한한다.
- summary action은 항상 첫 번째 action이어야 하며, slack action은 notify channel이 존재할 때만 선택 가능하다.
- LLM이 잘못된 plan을 반환하거나 비활성 상태면 deterministic fallback plan으로 전환하고 provenance에 이유를 남긴다.

## Acceptance Criteria
- 새 planner 모듈이 추가되고 model registry routing rule에 `plan_actions`가 반영된다.
- task runtime 상태 응답에 `planning_provenance`가 포함된다.
- `notify_channel`이 있는 task 요청은 planner가 summary + slack 2-step plan을 만들 수 있다.
- LLM planner가 꺼져 있거나 실패하면 fallback plan이 동작하고 provenance에 fallback 사유가 남는다.
- 계약/런타임 테스트가 추가되고 stage 8 cycle을 통과한다.

## Risks
- planner 출력 형식이 불안정하면 executor 이전에 plan 검증이 자주 fallback될 수 있다.
- slack planning을 task workflow에 넣으면서 기존 summary-only 테스트와 충돌할 수 있다.
- 기존 micro-cycle과 self-eval에 영향을 주지 않도록 테스트 범위를 명확히 유지해야 한다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage8-w5-024`
- `bash scripts/run_micro_cycle.sh gate-review stage8-w5-024`
- `python3 -m unittest tests.test_agent_planner_contract tests.test_agent_planner_runtime tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-024 8`
