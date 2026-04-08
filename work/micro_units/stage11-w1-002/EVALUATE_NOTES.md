# Evaluate Notes

## QA Result Summary
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_agent_entrypoint_smoke tests.test_tool_cli_smoke tests.test_mcp_server_smoke tests.test_capability_manifest_runtime tests.test_stage11_contract` 결과 `39 tests OK`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 11` 결과 `pass: 64 / fail: 0 / skip: 4`
- HTTP `/api/v1/agent/handoff/{task_id}`, CLI `newclaw handoff`, MCP `agent.handoff`가 모두 completed / approval-pending / blocked operator packet 분류를 반환하는 runtime smoke를 통과했다.
- capability manifest도 `agent.handoff`를 safe upper-agent surface로 노출하고, 관련 문서와 contract가 일치하는 것을 확인했다.

## Skip/Failure Reasons
- skip 4건은 기존 환경 의존 항목이며 Stage 11 G2 handoff packet export와 무관하다.
- `browser swagger smoke`: Playwright session `newclaw-browser-smoke` 미가용
- `postgres rehearsal smoke`: `NEWCLAW_DATABASE_URL` 미설정
- `stage8 sandbox rehearsal`: `NEWCLAW_STAGE8_SANDBOX_ENABLED` 미설정
- `stage8 live rehearsal`: `NEWCLAW_STAGE8_LIVE_ENABLED` 미설정
- handoff packet 추가로 인한 신규 failure는 없었다.

## Next Action
- `stage11-w1-002`는 sync 후 `DONE`으로 닫고, 다음 item `stage11-w1-003`를 prepare 한다.
- 다음 포커스는 local dev / sidecar operator / upper-agent host가 같은 deployment bootstrap profile을 쓰게 만드는 G3다.
