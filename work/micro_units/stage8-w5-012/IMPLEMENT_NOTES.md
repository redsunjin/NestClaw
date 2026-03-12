# Implement Notes

## Changed Files
- `app/main.py`
  - Added `internal.summary.generate` task planning helper.
  - Added shared `execution_call` dispatch path for `provider_invoker` and `redmine_mcp`.
  - Persisted `planned_actions` and `action_results` for both task and incident workflows.
- `app/services/orchestration_service.py`
  - Exposed `planned_actions`, `action_results`, and legacy `action_cards` in status payloads.
- `configs/tool_registry.yaml`
  - Registered `internal.summary.generate` as an internal tool capability.
- `tests/test_tool_registry_contract.py`
- `tests/test_tool_registry_runtime.py`
- `tests/test_provider_invoker_runtime.py`
- `tests/test_incident_runtime_smoke.py`
- `tests/test_tool_cli_smoke.py`
- `tests/test_mcp_server_smoke.py`
- `tests/test_stage8_contract.py`
  - Updated runtime and contract assertions for the shared planner/executor shape.

## Rollback Plan
- Revert this MWU commit to restore the previous split task/incident execution paths.
- Remove `internal.summary.generate` from `configs/tool_registry.yaml` if the unified tool surface needs to be backed out independently.

## Known Risks
- `planned_actions` currently unifies `meeting_summary` and incident ticket creation only. Additional tool families still need dedicated planner coverage.
- Incident policy review still runs through the incident-specific gate helper. This MWU only unifies the execution contract after planning.
