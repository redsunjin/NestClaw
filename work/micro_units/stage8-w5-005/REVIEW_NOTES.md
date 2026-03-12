# Review Notes

## Security / Policy Review
- MCP tool도 CLI/HTTP와 같은 actor identity/role 검증을 강제해야 한다.
- approval approve/reject tool은 `acted_by == actor_id` 규칙을 그대로 유지해야 한다.
- tool output은 JSON 구조를 유지하되 오류 시에도 식별 가능한 code/message를 남겨야 한다.

## Architecture / Workflow Review
- 이번 단위는 외부 AI가 사용할 표준 tool surface의 최소 골격을 만드는 작업이다.
- 별도 SDK 의존성 없이 stdio JSON-RPC와 service layer direct call로 시작하는 것이 현재 저장소에 가장 맞다.
- `resources`/`prompts`로 확장하기 전에 `tools/list`와 `tools/call` 안정성이 우선이다.
- tool schema는 CLI 명령과 1:1 대응을 유지해야 한다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `python3 -m unittest tests.test_tool_cli_smoke tests.test_mcp_server_smoke`
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-005 8`
- QA worktree에서는 실제 subprocess stdio smoke를 돌려 script entrypoint와 framing을 검증한다.

## Review Verdict
- 조건부 승인 (Approved as Minimal MCP Surface)
- 조건:
  1. tool 이름은 방향 문서와 정확히 일치할 것
  2. stdio transport는 Content-Length framing을 지킬 것
  3. `resources`/`prompts`까지 확장하지 말고 tool surface에 집중할 것
