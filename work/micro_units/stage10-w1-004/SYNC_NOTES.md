# Sync Notes

## Release Actions
- MCP stdio baseline과 upper-agent integration 경계를 새 가이드 문서로 고정했다.
- README / integration spec / examples / capability manifest가 같은 transport boundary를 말하도록 정리했다.
- MCP initialize instruction과 manifest transport metadata를 통해 upper-agent가 startup 시 stdio baseline과 elevated control 경계를 읽을 수 있게 했다.

## QA Sync Evidence
- `work/micro_units/stage10-w1-004/reports/plan-gate-20260405T102025Z.md`
- `work/micro_units/stage10-w1-004/reports/review-gate-20260405T102113Z.md`
- `reports/qa/cycle-20260405T121316Z.md`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_capability_manifest_runtime tests.test_tool_cli_smoke tests.test_mcp_server_smoke tests.test_stage10_contract`

## Final State
- `stage10-w1-004`는 MCP transport/deployment hardening baseline을 고정했고 evaluate 기준을 통과했다.
- `stage10-priority-campaign`은 G1~G4를 모두 완료한 상태로 닫을 수 있다.
- 이후 우선순위는 Stage 8 external env 재시도 또는 다음 campaign 정의다.
