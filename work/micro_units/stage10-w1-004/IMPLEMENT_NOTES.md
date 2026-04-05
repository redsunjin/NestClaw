# Implement Notes

## Changed Files
- `NESTCLAW_MCP_TRANSPORT_DEPLOYMENT_GUIDE.md`
- `NESTCLAW_AGENT_INTEGRATION_SPEC.md`
- `NESTCLAW_INTEGRATION_EXAMPLES.md`
- `NESTCLAW_CAPABILITY_MANIFEST.md`
- `README.md`
- `app/services/capability_manifest_service.py`
- `app/mcp_server.py`
- `app/cli.py`
- `tests/test_capability_manifest_runtime.py`
- `tests/test_tool_cli_smoke.py`
- `tests/test_mcp_server_smoke.py`
- `tests/test_stage10_contract.py`
- `work/micro_units/stage10-w1-004/PLAN_NOTES.md`
- `work/micro_units/stage10-w1-004/REVIEW_NOTES.md`

## Rollback Plan
- 이번 단계는 transport/deployment guidance와 capability metadata를 추가하는 작업이라, 문제가 생기면 MCP guide 문서와 manifest/server instruction 변경만 되돌리면 된다.
- runtime core action loop나 approval semantics는 건드리지 않았으므로, `transport.mcp` manifest 필드와 MCP initialize instruction 문자열만 제거해도 기존 실행 계약은 유지된다.
- README/spec/examples 변경도 additive라, 통합자가 혼동하면 새 guide 링크와 stdio boundary 설명만 되돌려 복구할 수 있다.

## Known Risks
- manifest에 `transport.mcp`를 추가했지만, 현재는 stdio baseline만 설명하므로 실제 remote deployment를 기대하는 사용자는 여전히 별도 wrapper가 필요하다.
- MCP initialize instruction은 간단한 운영 힌트 수준이라, 복잡한 auth topology를 대신 설명할 수는 없다.
- guide 문서가 현재 repo 구조와 어긋나지 않도록 이후 transport 구현이 추가되면 업데이트가 필요하다.
