# Review Notes

## Security / Policy Review
- live mode는 기본 비활성화 상태를 유지하고, `NEWCLAW_STAGE8_LIVE_ENABLED=1`과 MCP endpoint가 함께 있을 때만 실행 가능해야 한다.
- 요청 payload와 리포트에는 `token`, `password`, `secret`, `api_key` 등 민감 필드를 마스킹해야 한다.
- live rehearsal script는 운영 ticket lifecycle을 건드리므로 sandbox project/assignee/transition 값을 env로 명시적으로 받게 한다.
- credential이 없거나 live enable flag가 꺼져 있으면 실패 대신 `SKIP`로 종료해 오동작을 막아야 한다.

## Architecture / Workflow Review
- Stage 8 closeout 이후 후속 작업이므로 기존 G1~G4 self-eval 점수 모델은 유지하고, live rehearsal은 별도 MWU/운영 증적으로 관리한다.
- incident runtime은 `RAG context`와 `MCP execution`을 분리해 `mcp-live` 모드에서 외부 실행만 단계적으로 활성화한다.
- live endpoint 계약은 method/payload/actor_context를 받는 generic HTTP bridge로 제한해 특정 vendor path에 하드코딩하지 않는다.
- feature worktree에서 구현/문서화를 마치고 QA worktree에서는 fast-forward 후 live rehearsal script를 재검증한다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_stage8_contract tests.test_incident_adapter_contract`
  - `python3 -m unittest tests.test_incident_runtime_smoke`
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-001 8`
- 운영 검증:
  - QA worktree에서 `bash scripts/run_stage8_live_rehearsal.sh`
  - credential 부재 시 `SKIP` 리포트를 남기고, 이후 운영 슬롯에서 실제 `PASS` 증적으로 교체한다.

## Review Verdict
- 조건부 승인 (Approved with Live Guardrails)
- 조건:
  1. 기본 incident create/run 동작은 계속 dry-run 안전값을 유지해야 한다.
  2. `mcp-live`는 RAG live 호출을 유발하면 안 된다.
  3. live rehearsal script는 env/credential 부재 시 거짓 PASS를 만들면 안 된다.
