# Implement Notes

## Changed Files
- `app/tool_registry.py`
- `app/services/tool_draft_service.py`
- `app/main.py`
- `app/cli.py`
- `app/mcp_server.py`
- `scripts/run_tool_registry_maintenance.sh`
- `tests/test_tool_registry_contract.py`
- `tests/test_tool_draft_runtime.py`
- `tests/test_tool_cli_smoke.py`
- `tests/test_mcp_server_smoke.py`
- `tests/test_stage8_contract.py`

## Implementation Summary
- tool registry utility에 validation, overlay remove, overlay compact 기능을 추가했다.
- tool draft service에 `validate_draft`와 `rollback_tool`을 추가하고 apply 전에 validation gate를 강제했다.
- main runtime에 tool registry history snapshot과 rollback helper를 넣어 overlay apply/rollback을 안전하게 추적하도록 만들었다.
- API, CLI, MCP 모두 validation/rollback surface를 노출해 operator와 상위 agent가 같은 governance 절차를 사용하게 했다.
- maintenance script를 추가해 overlay status/validate/compact를 반복 가능한 운영 명령으로 묶었다.

## Rollback Plan
- `tool-validate`, `tool-rollback`, `catalog.validate_draft`, `catalog.rollback_tool` surface를 제거하고 기존 create/get/apply-only flow로 되돌린다.
- `app/tool_registry.py`의 validation/compact/remove helper를 제거하고 기존 upsert-only overlay path로 복구한다.
- `app/main.py`의 history snapshot 및 rollback helper를 제거해 overlay apply만 남긴다.

## Known Risks
- validation rule이 현재 known adapter 세트에 의존하므로 새 adapter 추가 시 rules를 같이 갱신해야 한다.
- rollback은 latest apply history 기준이므로 수동 파일 수정이 history 바깥에서 일어나면 정확도가 떨어질 수 있다.
- maintenance script는 운영 보조 도구라서 잘못된 cwd에서 실행되면 잘못된 overlay path를 볼 수 있다.
