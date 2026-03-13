# Plan Notes

## Scope
- tool draft를 approver/admin이 apply할 수 있는 경로를 추가한다.
- production source registry를 수정하지 않고 overlay registry 파일에 approved tool을 upsert한다.
- apply 직후 API/CLI/MCP catalog가 새 tool을 바로 보도록 runtime refresh를 연결한다.

## Out of Scope
- tool draft approval queue 일반화
- draft diff / rollback UI
- tool execution dependency graph 확장

## Acceptance Criteria
- approver/admin만 draft apply를 수행할 수 있다.
- apply 후 overlay registry 파일이 생성/갱신된다.
- 같은 프로세스의 API/CLI/MCP catalog surface가 새 tool을 즉시 반환한다.
- overlay/apply 흐름에 대한 계약 및 runtime tests가 추가된다.

## Risks
- overlay merge가 잘못되면 catalog와 planner가 다른 registry를 볼 수 있다.
- apply 권한을 requester에게 열면 정책 우회가 되므로 반드시 approver/admin으로 제한해야 한다.
- 테스트 중 생성된 overlay/draft 산출물을 정리하지 않으면 worktree가 더러워질 수 있다.

## Test Plan
- `python3 -m unittest tests.test_tool_registry_contract tests.test_tool_draft_runtime tests.test_tool_cli_smoke tests.test_mcp_server_smoke tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-014 8`
