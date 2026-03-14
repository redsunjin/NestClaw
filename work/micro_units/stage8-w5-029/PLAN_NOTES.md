# Plan Notes

## Scope
- tool draft에 대해 명시적인 validation report를 만들고, apply 전에 validation을 강제한다.
- applied tool에 대한 rollback path를 추가해 runtime overlay에서 마지막 변경을 안전하게 되돌릴 수 있게 만든다.
- overlay registry를 validate/compact/status 할 수 있는 maintenance script를 추가한다.
- API, CLI, MCP surface를 validation/rollback까지 확장해 operator와 상위 agent가 같은 절차를 사용할 수 있게 만든다.

## Out of Scope
- GUI에서 rollback 버튼 추가
- live external tool invocation 확대
- tool schema version migration까지의 대규모 설계 변경
- approval workflow 자체 재설계

## AI-First Planner Design
- AI planner가 사용할 tool surface는 governance가 안정적이어야 하므로, validation과 rollback은 planner 신뢰도와 직접 연결된다.
- planner는 registry를 신뢰하고 tool을 고르므로, registry mutation은 deterministic validation gate를 거쳐야 한다.
- rollback은 planner fallback이 아니라 governance control plane 기능이며, operator와 상위 agent가 같은 surface로 호출 가능해야 한다.
- maintenance script는 AI planner runtime이 아닌 운영 계층이지만, planner가 읽는 overlay를 일관된 상태로 유지하는 역할을 맡는다.

## Acceptance Criteria
- draft validation endpoint/CLI/MCP surface가 존재하고 validation report를 반환한다.
- apply_draft는 invalid spec를 차단하고 valid spec만 overlay에 반영한다.
- rollback surface가 마지막 overlay change를 되돌리고 catalog에서 반영 결과를 확인할 수 있다.
- maintenance script가 overlay validate/status/compact를 수행할 수 있다.
- stage 8 micro-cycle과 QA canonical cycle이 통과한다.

## Risks
- rollback history를 불완전하게 저장하면 restore가 실패할 수 있다.
- validation 규칙이 너무 엄격하면 legitimate custom tool 등록을 막을 수 있다.
- compact가 잘못 구현되면 overlay에서 필요한 tool을 삭제할 수 있으므로 base/overlay 비교를 보수적으로 해야 한다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage8-w5-029`
- `bash scripts/run_micro_cycle.sh gate-review stage8-w5-029`
- `python3 -m unittest tests.test_tool_registry_contract tests.test_tool_draft_runtime tests.test_tool_cli_smoke tests.test_mcp_server_smoke tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-029 8`
