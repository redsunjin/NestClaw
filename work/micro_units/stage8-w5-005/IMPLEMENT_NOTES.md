# Implement Notes

## Changed Files
- [x] `app/mcp_server.py`
  - stdio Content-Length framing 기반 최소 MCP server 추가
  - `initialize`, `notifications/initialized`, `ping`, `tools/list`, `tools/call` 구현
  - sync service layer를 재사용해 `agent.*`, `approval.*` tool 제공
- [x] `tests/test_mcp_server_smoke.py`
  - 실제 subprocess stdio framing smoke 추가
  - `tools/list`, `agent.submit/status`, `approval.list/approve/reject` 경로 검증
- [x] `tests/test_stage8_contract.py`
  - MCP server/stdio smoke 파일 존재 및 required tool surface 계약 추가
- [x] `scripts/run_dev_qa_cycle.sh`
  - stage8 MCP server smoke를 QA cycle에 연결
- [x] `README.md`
  - MCP server 실행 경로와 제공 tool 목록 추가
- [x] `TASKS.md`
  - MCP server backlog 항목 완료 반영
- [x] `NEXT_STAGE_PLAN_2026-02-24.md`
  - 다음 우선순위를 model routing/operator UI 중심으로 조정
- [x] `work/micro_units/stage8-w5-005/*`
  - MWU plan/review/implement/evaluate 자산 추가

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `app/mcp_server.py`
  - `tests/test_mcp_server_smoke.py`
  - `tests/test_stage8_contract.py`
  - `scripts/run_dev_qa_cycle.sh`
  - `README.md`
  - `TASKS.md`
  - `NEXT_STAGE_PLAN_2026-02-24.md`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- 현재 MCP server는 stdio transport와 tool surface만 제공하며, streamable HTTP/resources/prompts는 아직 없다.
- sync execution tool은 길게 걸리는 workflow를 모두 안전하게 감싸지 못할 수 있다.
- feature worktree에서는 runtime dependency 부재로 일부 smoke가 `SKIP`될 수 있다.
