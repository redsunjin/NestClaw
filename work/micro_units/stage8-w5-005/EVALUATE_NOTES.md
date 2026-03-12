# Evaluate Notes

## QA Result Summary
- 검증 명령:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `env PATH="/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-mcp-feature.db python3 -m unittest tests.test_tool_cli_smoke tests.test_mcp_server_smoke`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db python3 -m unittest tests.test_spec_contract tests.test_stage8_contract tests.test_tool_cli_smoke tests.test_mcp_server_smoke`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-005 8`
- 결과:
  - feature contract tests: PASS (`30 tests`)
  - feature MCP/CLI runtime preflight bundle: PASS (`8 tests`)
  - QA runtime + contract bundle: PASS (`38 tests`)
  - QA worktree stage 8 dev qa cycle: PASS (`/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/cycle-20260312T074104Z.md`)
  - feature micro-cycle: PASS (`work/micro_units/stage8-w5-005/reports/evaluate-gate-20260312T074140Z.md`)

## Skip/Failure Reasons
- sandbox/live rehearsal은 이번 단위 범위 밖이라 env 미설정 시 계속 `SKIP`이다.
- stage8 grouped self-eval은 nested cycle 방지를 위해 `NEWCLAW_SKIP_STAGE8_SELF_EVAL=1`로 의도적으로 skip 했다.

## Next Action
- 다음 우선순위는 model registry runtime loader와 provider selection logging, 이후 LLM intent classifier 연결이다.
- feature cycle evidence: `reports/qa/cycle-20260312T074140Z.md`
