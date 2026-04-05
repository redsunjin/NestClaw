# Evaluate Notes

## QA Result Summary
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_web_console_runtime tests.test_stage8_contract tests.test_stage9_contract tests.test_stage10_contract tests.test_agent_entrypoint_smoke tests.test_tool_cli_smoke tests.test_mcp_server_smoke` 결과 `81 tests OK`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 10` 결과 `pass: 62 / fail: 0 / skip: 4`
- quickstart/console role gating 변경 후에도 stage10 bundle surface, agent facade, CLI, MCP smoke는 모두 유지됐다.
- requester/reviewer용 읽기 중심 copy와 approver/admin용 운영 제어면 분리가 정적/runtime 테스트에서 확인됐다.

## Skip/Failure Reasons
- skip 4건은 기존 환경 의존 항목이며 이번 UI 변경과 무관하다.
- `browser swagger smoke`: Playwright session `newclaw-browser-smoke` 미가용
- `postgres rehearsal smoke`: `NEWCLAW_DATABASE_URL` 미설정
- `stage8 sandbox rehearsal`: `NEWCLAW_STAGE8_SANDBOX_ENABLED` 미설정
- `stage8 live rehearsal`: `NEWCLAW_STAGE8_LIVE_ENABLED` 미설정
- role gating 변경으로 인한 신규 failure는 없었다.

## Next Action
- `stage10-w1-002`는 sync 후 `DONE`으로 닫고, 다음 item `stage10-w1-003`를 prepare 한다.
- 다음 포커스는 readiness / error taxonomy normalization이다.
