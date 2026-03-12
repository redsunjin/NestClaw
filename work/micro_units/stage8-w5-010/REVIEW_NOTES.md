# Review Notes

## Security / Policy Review
- tool registry는 곧 allowlist 역할을 하므로, catalog에 없는 도구가 실행 경로에 직접 들어가지 않게 해야 한다.
- capability schema에는 `risk_level`, `approval_required`, `external_system` 같은 정책 판단에 필요한 최소 정보가 남아야 한다.
- catalog 조회 표면은 정의 조회만 제공하고, 실행 권한과 별도로 분리한다.

## Architecture / Workflow Review
- 현재 제품은 `agent facade + task/incident workflow family + CLI/MCP/API` 구조이므로 registry는 이 공통 코어 위에 올라가야 한다.
- 첫 단계에서는 현재 incident Redmine action을 registry의 concrete consumer로 삼고, planner 일반화는 다음 단계로 미룬다.
- MCP에는 protocol `tools/list` 외에 business catalog 조회용 tool을 별도로 추가하는 것이 맞다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_tool_registry_contract tests.test_tool_cli_smoke tests.test_mcp_server_smoke tests.test_incident_runtime_smoke tests.test_stage8_contract`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-010 8`
- action-card / CLI / MCP / API 중 한 표면만 맞추는 식의 부분 구현은 불합격이다.

## Review Verdict
- 승인 (Approved with Minimal Capability Schema)
- 조건:
  1. registry는 현재 실행 경로를 설명 가능한 수준까지 도입하되, 기존 action-card 계약은 깨지지 않게 유지할 것
  2. catalog tool 명칭은 MCP protocol과 혼동되지 않게 할 것
  3. incident use case를 첫 concrete consumer로 연결할 것
