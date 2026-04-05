# Plan Notes

## Scope
- existing `agent.bundle`와 `status/report/approval` evidence를 기반으로 operator handoff packet shape를 정의한다.
- blocked, approval-pending, completed 세 상태에 대해 operator가 바로 판단할 수 있는 최소 필드를 markdown/json export 기준으로 고정한다.
- 가능하면 HTTP/CLI/MCP 중 최소 두 표면 이상에서 같은 packet contract를 읽을 수 있게 하고, role gating도 함께 유지한다.
- operator dashboard나 상위 agent가 handoff 시 재구성 로직을 덜 갖도록 canonical packet summary를 제공하는 방향을 검토한다.

## Out of Scope
- 새로운 planner/provider/tool execution 로직 추가
- Stage 8 external env 자체 발급
- dashboard chat panel 도입
- remote MCP transport 구현
- pilot acceptance policy 변경

## AI-First Planner Design
- 이번 단계는 planner intelligence를 확장하는 작업이 아니라, planner/executor가 남긴 결과를 operator에게 어떻게 compact하게 handoff 할지에 대한 control-plane 작업이다.
- 이미 있는 `agent.bundle`, `status`, `approval`, `report`를 조합하되, 상위 agent와 operator가 같은 vocabulary를 읽도록 `blocked`, `approval-pending`, `done` 상태별 packet shape를 고정하는 편이 맞다.
- handoff packet은 새로운 truth source가 아니라 기존 execution evidence의 view model이어야 하며, approval policy나 audit trail을 우회하면 안 된다.
- 따라서 packet export는 additive surface로 설계하고, role별로 볼 수 있는 detail 범위를 분리하는 방향이 적절하다.

## Acceptance Criteria
- operator handoff packet의 canonical field set이 문서 또는 코드로 정의된다.
- 최소 blocked / approval-pending / completed 세 상태에서 필요한 summary field가 고정된다.
- packet export가 기존 execution bundle과 모순되지 않고, role gating을 유지한다.
- 관련 contract/test와 `bash scripts/run_dev_qa_cycle.sh 11`이 통과한다.
- operator가 현재 상태, next action, approval requirement, report/report preview 유무를 packet 하나로 읽을 수 있다.

## Risks
- packet에 approval detail이나 raw report를 과도하게 담으면 requester/reviewer에게 과한 정보가 노출될 수 있다.
- bundle과 packet이 서로 다른 naming을 쓰기 시작하면 upper-agent/operator handoff가 오히려 복잡해질 수 있다.
- blocked와 fail, approval-pending을 섞어 요약하면 운영자 판단이 흐려질 수 있다.
- markdown/json dual export를 동시에 다루면 contract drift가 생길 수 있으므로 canonical source를 하나로 정해야 한다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage11-w1-002`
- `bash scripts/run_micro_cycle.sh gate-review stage11-w1-002`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_stage11_contract`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 11`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_micro_cycle.sh run stage11-w1-002 11`
