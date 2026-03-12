# Evaluate Notes

## QA Result Summary
- 검증 명령:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `env PATH="/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-cli-feature.db python3 -m unittest tests.test_agent_entrypoint_smoke tests.test_incident_runtime_smoke tests.test_tool_cli_smoke`
  - `env PATH="/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-cli-feature.db python3 app/cli.py submit --requested-by qa_user --task-kind task --request-text "운영회의 요약" --metadata-json '{"meeting_title":"ops sync","meeting_date":"2026-03-12","participants":["Kim"],"notes":"internal only"}' --json`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db python3 -m unittest tests.test_spec_contract tests.test_stage8_contract tests.test_agent_entrypoint_smoke tests.test_incident_runtime_smoke tests.test_tool_cli_smoke`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-004 8`
- 결과:
  - feature contract tests: PASS (`29 tests`)
  - feature runtime preflight bundle: PASS (`13 tests`)
  - direct script entrypoint (`python3 app/cli.py ... --json`): PASS
  - QA runtime + contract bundle: PASS (`42 tests`)
  - QA worktree stage 8 dev qa cycle: PASS (`/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/cycle-20260312T072112Z.md`)
  - feature micro-cycle: PASS (`work/micro_units/stage8-w5-004/reports/evaluate-gate-20260312T072155Z.md`)

## Skip/Failure Reasons
- sandbox/live rehearsal은 이번 단위 범위 밖이라 env 미설정 시 계속 `SKIP`이다.
- stage8 grouped self-eval은 nested cycle 방지를 위해 `NEWCLAW_SKIP_STAGE8_SELF_EVAL=1`로 의도적으로 skip 했다.

## Next Action
- 다음 우선순위는 MCP server를 추가해 `agent.submit/status/events`, `approval.*`를 외부 AI tool surface로 노출하는 것이다.
- feature cycle evidence: `reports/qa/cycle-20260312T072155Z.md`
