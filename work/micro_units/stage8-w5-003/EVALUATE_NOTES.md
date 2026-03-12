# Evaluate Notes

## QA Result Summary
- 검증 명령:
  - `env PYTHONPYCACHEPREFIX=.pycache python3 -m py_compile app/main.py app/services/__init__.py app/services/orchestration_service.py tests/test_stage8_contract.py`
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db python3 -m unittest tests.test_spec_contract tests.test_stage8_contract tests.test_runtime_smoke tests.test_agent_entrypoint_smoke tests.test_incident_runtime_smoke`
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 8`
- 결과:
  - 정적 compile: PASS
  - feature contract tests: PASS (`28 tests`)
  - QA runtime + contract bundle: PASS (`44 tests`)
  - feature worktree stage 8 dev qa cycle: PASS (`reports/qa/cycle-20260312T040200Z.md`)
  - QA worktree stage 8 dev qa cycle: PASS (`/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/cycle-20260312T040557Z.md`)

## Skip/Failure Reasons
- 최초 구현 직후 QA runtime에서 `OrchestrationService -> _set_status` 계약 회귀가 있었고, `TaskStatus` enum 대신 문자열을 넘겨 `AttributeError: 'str' object has no attribute 'value'`가 발생했다.
- `583cb8f`에서 service deps를 enum 기반으로 되돌리고 저장/응답만 문자열로 normalize 하도록 수정한 뒤 회귀가 해소됐다.
- sandbox/live rehearsal은 이번 단위 범위 밖이라 env 미설정 시 계속 `SKIP`이다.

## Evidence
- feature service extraction commit: `8cfc37a`
- regression fix commit: `583cb8f`
- QA runtime bundle: `44 tests` PASS
- QA cycle report: `/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/cycle-20260312T040557Z.md`
- feature micro-cycle evaluate gate: `work/micro_units/stage8-w5-003/reports/evaluate-gate-20260312T040647Z.md`
- feature cycle report captured by micro-cycle: `reports/qa/cycle-20260312T040648Z.md`

## Next Action
- 다음 follow-up은 `app/services/`를 기반으로 비대화형 CLI와 MCP tool surface를 추가하는 것이다.
- Stage 8 전체 readiness를 다시 `8/8`로 올리려면 별도 QA session에서 sandbox/live rehearsal env를 채워 G4를 닫아야 한다.
