# Implement Notes

## Changed Files
- [x] `configs/tool_registry.yaml`
  - Redmine execution tool catalog와 capability metadata를 초기 등록
- [x] `app/tool_registry.py`
  - tool registry loader, capability schema, filter/get helper 추가
- [x] `app/services/tool_catalog_service.py`
  - 공통 tool catalog service 계층 추가
- [x] `app/services/__init__.py`
  - tool catalog service export 추가
- [x] `app/main.py`
  - `TOOL_REGISTRY` load, incident action-card registry 연동, `/api/v1/tools` surface 추가
- [x] `app/cli.py`
  - `tools` non-interactive command 추가
- [x] `app/mcp_server.py`
  - `catalog.list`, `catalog.get` business tools 추가
- [x] `tests/test_tool_registry_contract.py`
  - registry 설정/loader/filter 계약 검증 추가
- [x] `tests/test_tool_registry_runtime.py`
  - tools API 및 incident runtime registry 연동 smoke 추가
- [x] `tests/test_tool_cli_smoke.py`
  - CLI `tools` command smoke 추가
- [x] `tests/test_mcp_server_smoke.py`
  - MCP catalog tools smoke 추가
- [x] `tests/test_incident_runtime_smoke.py`
  - incident action-card에 registry metadata가 남는지 검증 추가
- [x] `tests/test_stage8_contract.py`
  - registry/catalog wiring 정적 계약 추가
- [x] `scripts/run_dev_qa_cycle.sh`
  - stage8 tool registry contract/runtime checks 추가
- [x] `README.md`, `TASKS.md`, `NEXT_STAGE_PLAN_2026-02-24.md`, `API_CONTRACT.md`, `AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md`
  - registry 도입 후 현재 상태와 다음 우선순위 반영

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `configs/tool_registry.yaml`
  - `app/tool_registry.py`
  - `app/services/tool_catalog_service.py`
  - `app/main.py`
  - `app/cli.py`
  - `app/mcp_server.py`
  - `tests/test_tool_registry_contract.py`
  - `tests/test_tool_registry_runtime.py`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_tool_registry_contract tests.test_stage8_contract`
  - `env PATH="/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- 현재 registry는 catalog/allowlist와 incident Redmine create consumer까지만 연결돼 있고, planner 일반화는 아직 아니다.
- capability schema를 단순 scalar 중심으로 시작했기 때문에 복합 payload schema가 필요해지면 확장 작업이 필요하다.
- catalog surface는 추가됐지만 provider invocation/live execution 통합은 다음 단계다.
