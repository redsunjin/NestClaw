# Evaluate Notes

## QA Result Summary
- 검증 명령:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `python3 -m unittest tests.test_model_registry_contract`
  - `env PATH="/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-model-feature.db python3 -m unittest tests.test_model_registry_runtime tests.test_agent_entrypoint_smoke tests.test_incident_runtime_smoke`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db python3 -m unittest tests.test_spec_contract tests.test_stage8_contract tests.test_model_registry_contract tests.test_model_registry_runtime tests.test_agent_entrypoint_smoke tests.test_incident_runtime_smoke`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-006 8`
- 결과:
  - feature contract + unit tests: PASS (`36 tests`)
  - feature runtime preflight bundle: PASS (`11 tests`)
  - QA runtime + contract bundle: PASS (`47 tests`)
  - QA worktree stage 8 dev qa cycle: PASS (`/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/cycle-20260312T075228Z.md`)
  - feature micro-cycle: PASS (`work/micro_units/stage8-w5-006/reports/evaluate-gate-20260312T075302Z.md`)

## Skip/Failure Reasons
- sandbox/live rehearsal은 이번 단위 범위 밖이라 env 미설정 시 계속 `SKIP`이다.
- stage8 grouped self-eval은 nested cycle 방지를 위해 `NEWCLAW_SKIP_STAGE8_SELF_EVAL=1`로 의도적으로 skip 했다.

## Next Action
- 다음 우선순위는 heuristic `task_kind=auto`를 LLM intent classifier로 교체하고, 이어서 model registry selection을 실제 provider invocation에 연결하는 것이다.
- feature cycle evidence: `reports/qa/cycle-20260312T075302Z.md`
