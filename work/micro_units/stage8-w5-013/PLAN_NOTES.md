# Plan Notes

## Scope
- Slack execution capability를 tool registry와 runtime dispatcher에 추가한다.
- incident workflow가 `notify_channel`이 주어지면 Slack notification action도 계획하도록 확장한다.
- 사람이 직접 파일을 고치지 않아도 AI assistant가 reviewable draft를 만들 수 있도록 tool draft registration surface를 API/CLI/MCP에 추가한다.

## Out of Scope
- draft를 production tool registry에 자동 반영하는 기능
- Slack 외 다른 외부 시스템 adapter 추가
- multi-step dependency resolution 고도화

## Acceptance Criteria
- `slack.message.send`가 catalog에 노출된다.
- incident workflow가 Slack channel 입력 시 Slack action을 계획/실행한다.
- tool draft를 API/CLI/MCP에서 생성하고 다시 조회할 수 있다.
- Slack adapter와 tool draft surface에 대한 테스트가 추가된다.

## Risks
- tool draft를 바로 production registry에 반영하면 policy 우회가 될 수 있으므로 draft-only로 제한해야 한다.
- Slack notification을 incident planner에 넣을 때 기존 approval semantics를 깨면 안 된다.
- draft 생성이 너무 느슨하면 adapter/method 추정이 부정확할 수 있다.

## Test Plan
- `python3 -m unittest tests.test_slack_adapter_contract tests.test_tool_draft_runtime tests.test_tool_registry_contract tests.test_tool_registry_runtime tests.test_tool_cli_smoke tests.test_mcp_server_smoke tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-013 8`
