# Evaluate Notes

## QA Result Summary
- 검증 명령:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract tests.test_model_registry_contract tests.test_intent_classifier_contract`
  - `env PATH="/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-lmstudio-feature.db python3 -m unittest tests.test_intent_classifier_runtime tests.test_agent_entrypoint_smoke tests.test_model_registry_runtime`
  - `env PATH="/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-lmstudio-feature.db NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 8`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db python3 -m unittest tests.test_spec_contract tests.test_stage8_contract tests.test_model_registry_contract tests.test_intent_classifier_contract tests.test_incident_adapter_contract tests.test_incident_policy_gate tests.test_model_registry_runtime tests.test_intent_classifier_runtime tests.test_agent_entrypoint_smoke tests.test_incident_runtime_smoke tests.test_tool_cli_smoke tests.test_mcp_server_smoke`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 8`
  - `curl http://localhost:1234/v1/models`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_ENABLE_LLM_INTENT=1 NEWCLAW_LMSTUDIO_BASE_URL=http://localhost:1234 NEWCLAW_INTENT_CLASSIFIER_TIMEOUT=20 NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-lmstudio.db python3 app/cli.py submit --requested-by qa_user --task-kind auto --request-text "billing-api 장애 대응 티켓을 생성해줘" --metadata-json '{"service":"billing-api","severity":"low","time_window":"15m"}' --json`
- 결과:
  - feature contract bundle: PASS (`43 tests`)
  - feature runtime preflight bundle: PASS (`7 tests`)
  - feature Stage 8 dev-qa cycle: PASS (`reports/qa/cycle-20260312T112624Z.md`)
  - QA runtime + contract bundle: PASS (`80 tests`)
  - QA Stage 8 dev-qa cycle: PASS (`/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/cycle-20260312T112821Z.md`)
  - QA live endpoint probe: PASS (`curl http://localhost:1234/v1/models` returned loaded model list)
  - QA live classifier call: SAFE_FALLBACK (`intent_classification.source=llm_error_fallback`, `fallback_reason=timed out`)

## Skip/Failure Reasons
- sandbox/live rehearsal은 이번 단위 범위 밖이라 env 미설정 상태에서는 계속 `SKIP`이다.
- LM Studio endpoint 자체는 살아 있지만 loaded model 응답이 20초 timeout 안에 끝나지 않아 classifier는 heuristic fallback으로 마감됐다.

## Next Action
- 다음 우선순위는 LM Studio/OpenAI-compatible selection을 broader provider invocation으로 확장하고, 느린 local model에 맞는 timeout/model pinning 정책을 정리하는 것이다.
