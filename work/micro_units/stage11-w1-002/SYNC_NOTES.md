# Sync Notes

## Release Actions
- compact operator handoff packet spec을 추가하고, `agent.bundle` 기반 compact view model을 HTTP/CLI/MCP에 공통으로 열었다.
- operator handoff packet은 JSON canonical source + markdown rendering 구조로 제공하고, existing approval detail gating을 그대로 따른다.
- capability manifest, integration spec, examples, README도 새 handoff surface를 같은 vocabulary로 참조하도록 갱신했다.

## QA Sync Evidence
- `work/micro_units/stage11-w1-002/reports/plan-gate-20260405T123255Z.md`
- `work/micro_units/stage11-w1-002/reports/review-gate-20260406T151118Z.md`
- `work/micro_units/stage11-w1-002/reports/implement-gate-20260406T151458Z.md`
- `work/micro_units/stage11-w1-002/reports/evaluate-gate-20260406T151610Z.md`
- `reports/qa/cycle-20260406T151610Z.md`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_agent_entrypoint_smoke tests.test_tool_cli_smoke tests.test_mcp_server_smoke tests.test_capability_manifest_runtime tests.test_stage11_contract`

## Final State
- `stage11-w1-002`는 blocked / approval-pending / completed 상태를 compact operator packet으로 export 하는 baseline을 고정했고 Stage 11 cycle 기준을 통과했다.
- 상위 agent는 deeper audit이 필요할 때 `bundle`, operator handoff가 필요할 때 `handoff`를 쓰는 표면 분리가 가능해졌다.
- 다음 item은 `g3-deployment-profile-bootstrap`이다.
