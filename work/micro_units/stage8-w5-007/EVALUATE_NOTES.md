# Evaluate Notes

## QA Result Summary
- 검증 명령:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract tests.test_model_registry_contract tests.test_intent_classifier_contract`
  - `env PATH="/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-intent-feature.db python3 -m unittest tests.test_intent_classifier_runtime tests.test_agent_entrypoint_smoke tests.test_model_registry_runtime`
  - `env PATH="/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-intent-feature.db NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 8`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db python3 -m unittest tests.test_spec_contract tests.test_stage8_contract tests.test_model_registry_contract tests.test_intent_classifier_contract tests.test_incident_adapter_contract tests.test_incident_policy_gate tests.test_model_registry_runtime tests.test_intent_classifier_runtime tests.test_agent_entrypoint_smoke tests.test_incident_runtime_smoke tests.test_tool_cli_smoke tests.test_mcp_server_smoke`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 8`
  - `env PATH="/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-intent-feature.db bash scripts/run_micro_cycle.sh run stage8-w5-007 8`
- 결과:
  - feature contract bundle: PASS (`42 tests`)
  - feature runtime preflight bundle: PASS (`7 tests`)
  - feature Stage 8 dev-qa cycle: PASS (`reports/qa/cycle-20260312T105718Z.md`)
  - QA runtime + contract bundle: PASS (`79 tests`)
  - QA Stage 8 dev-qa cycle: PASS (`/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/cycle-20260312T105830Z.md`)
  - feature micro-cycle: PASS (`work/micro_units/stage8-w5-007/reports/evaluate-gate-20260312T110001Z.md`)

## Skip/Failure Reasons
- sandbox/live rehearsal은 이번 단위 범위 밖이라 env 미설정 상태에서는 계속 `SKIP`이다.
- nested cycle 방지를 위해 grouped self-eval baseline은 `NEWCLAW_SKIP_STAGE8_SELF_EVAL=1`로 의도적으로 skip 했다.

## Next Action
- 다음 우선순위는 model registry selection을 실제 provider invocation에 연결하고, 그 뒤 action-card/tool planning 공통 루프를 정리하는 것이다.
