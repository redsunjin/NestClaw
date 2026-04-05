# Evaluate Notes

## QA Result Summary
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_capability_manifest_runtime tests.test_agent_entrypoint_smoke tests.test_tool_cli_smoke tests.test_mcp_server_smoke tests.test_web_console_runtime tests.test_stage10_contract` 결과 `36 tests OK`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 10` 결과 `pass: 62 / fail: 0 / skip: 4`
- capability manifest, agent status/recent/bundle, CLI, MCP, quickstart, console가 모두 canonical taxonomy field를 읽도록 맞췄고 runtime smoke가 이를 검증했다.
- `stage10-w1-002` 완료 후 열렸던 `stage10-w1-003` campaign state와 stage10 contract도 새 baseline에 맞게 유지됐다.

## Skip/Failure Reasons
- skip 4건은 기존 환경 의존 항목이며 이번 taxonomy normalization과 무관하다.
- `browser swagger smoke`: Playwright session `newclaw-browser-smoke` 미가용
- `postgres rehearsal smoke`: `NEWCLAW_DATABASE_URL` 미설정
- `stage8 sandbox rehearsal`: `NEWCLAW_STAGE8_SANDBOX_ENABLED` 미설정
- `stage8 live rehearsal`: `NEWCLAW_STAGE8_LIVE_ENABLED` 미설정
- taxonomy normalization으로 인한 신규 failure는 없었다.

## Next Action
- `stage10-w1-003`은 sync 후 `DONE`으로 닫고, 다음 item `stage10-w1-004`를 prepare 한다.
- 다음 포커스는 MCP transport / deployment hardening이다.
