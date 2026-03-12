# Plan Notes

## Scope
- `app/mcp_server.py`에 stdio 기반 최소 MCP server를 추가한다.
- `initialize`, `notifications/initialized`, `tools/list`, `tools/call`, `ping` 범위를 구현한다.
- tool surface는 `agent.submit`, `agent.status`, `agent.events`, `approval.list`, `approval.approve`, `approval.reject`로 고정한다.
- tool execution은 기존 service layer를 sync mode로 직접 호출한다.
- MCP server 계약/stdio smoke 테스트와 문서를 추가한다.

## Out of Scope
- streamable HTTP transport
- MCP prompts/resources 지원
- 외부 MCP Python SDK 도입
- live sandbox credential이 필요한 rehearsal
- LLM intent router 연결

## Acceptance Criteria
- `python3 app/mcp_server.py`가 stdio JSON-RPC로 initialize/tools/list/tools/call을 처리한다.
- tool names가 방향 문서와 동일하게 노출된다.
- agent/approval tool 호출이 기존 service layer를 직접 사용한다.
- `tests.test_mcp_server_smoke`와 관련 contract tests가 통과한다.
- `bash scripts/run_micro_cycle.sh run stage8-w5-005 8`가 통과한다.

## Risks
- MCP framing(Content-Length) 구현을 잘못하면 실제 클라이언트와 호환되지 않을 수 있다.
- sync tool execution이 장기 실행 task에 모두 적합한 것은 아니므로 범위를 명확히 해야 한다.
- tool input schema와 실제 service 인자 사이가 어긋나면 호출 오류가 생길 수 있다.

## Test Plan
- 정적:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
- 런타임:
  - `python3 -m unittest tests.test_tool_cli_smoke tests.test_mcp_server_smoke`
- 품질 게이트:
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-005 8`
