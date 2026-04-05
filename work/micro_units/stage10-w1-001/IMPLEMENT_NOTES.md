# Implement Notes

## Changed Files
- `app/services/orchestration_service.py`
- `app/main.py`
- `app/cli.py`
- `app/mcp_server.py`
- `scripts/run_dev_qa_cycle.sh`
- `scripts/run_auto_cycle.sh`
- `README.md`
- `NESTCLAW_AGENT_INTEGRATION_SPEC.md`
- `NESTCLAW_CAPABILITY_MANIFEST.md`
- `NEXT_WORK_GROUPS_2026-04-05.md`
- `work/priority_campaigns/stage10-priority-campaign/campaign.json`
- `work/micro_units/stage10-w1-001/PLAN_NOTES.md`
- `work/micro_units/stage10-w1-001/REVIEW_NOTES.md`
- `tests/test_stage8_contract.py`
- `tests/test_stage9_contract.py`
- `tests/test_stage10_contract.py`
- `tests/test_agent_entrypoint_smoke.py`
- `tests/test_tool_cli_smoke.py`
- `tests/test_mcp_server_smoke.py`

## Rollback Plan
- `agent_bundle` surface만 되돌리면 기존 `status/events/report/approvals/capabilities` 개별 표면은 그대로 유지된다.
- 문제가 생기면 `app/services/orchestration_service.py`, `app/main.py`, `app/cli.py`, `app/mcp_server.py`에서 bundle route/command/tool을 제거하고 Stage 10 contract/test additions를 같이 되돌리면 된다.
- QA cycle stage10 확장(`scripts/run_dev_qa_cycle.sh`, `scripts/run_auto_cycle.sh`)은 bundle surface 제거 시 함께 1..9 기준으로 복귀시키면 된다.

## Known Risks
- bundle payload에 capability snapshot이 중첩되므로 응답 크기가 커질 수 있다.
- approval access level 정책이 느슨해지면 requester에게 detail이 노출될 수 있어 role regression을 계속 봐야 한다.
- stage10 cycle이 현재 agent facade/CLI/MCP smoke를 재사용하므로, 이후 더 세밀한 execution bundle 전용 runtime smoke가 추가로 필요할 수 있다.
