# Evaluate Notes

## QA Result Summary
- 검증 명령:
  - `python3 -m unittest tests.test_stage8_contract`
  - `python3 -m unittest tests.test_incident_adapter_contract`
  - `python3 -m unittest tests.test_incident_runtime_smoke`
  - `env PYTHONPYCACHEPREFIX=.pycache python3 -m py_compile app/main.py app/incident_mcp.py scripts/stage8_live_rehearsal_runner.py`
  - `bash scripts/run_stage8_live_rehearsal.sh`
  - `bash scripts/run_dev_qa_cycle.sh 8`
- 결과:
  - Stage 8 contract tests: PASS (`19 tests`)
  - incident adapter contract tests: PASS (`9 tests`)
  - incident runtime smoke: SKIP (`6 skipped`, feature worktree runtime dependency 부재)
  - live rehearsal script: SKIP (`reports/qa/stage8-live-rehearsal-20260306T152505Z.md`)
  - dev qa cycle stage 8: PASS (`reports/qa/cycle-20260306T152504Z.md`)
  - micro cycle: PASS (`bash scripts/run_micro_cycle.sh run stage8-w5-001 8`)
  - QA worktree unittest bundle: PASS (`34 tests`, `tests.test_stage8_contract`, `tests.test_incident_adapter_contract`, `tests.test_incident_runtime_smoke`)
  - QA worktree live rehearsal: SKIP (`reports/qa/stage8-live-rehearsal-20260306T164913Z.md`, `NEWCLAW_STAGE8_LIVE_ENABLED` 미설정)
  - QA worktree dev qa cycle stage 8: PASS (`reports/qa/cycle-20260306T164914Z.md`)
- 확보된 리포트:
  - `work/micro_units/stage8-w5-001/reports/plan-gate-20260306T152504Z.md`
  - `work/micro_units/stage8-w5-001/reports/review-gate-20260306T152504Z.md`
  - `work/micro_units/stage8-w5-001/reports/implement-gate-20260306T152504Z.md`
  - `work/micro_units/stage8-w5-001/reports/evaluate-gate-20260306T152504Z.md`
  - `work/micro_units/stage8-w5-001/reports/evaluate-cycle-20260306T152505Z.log`
  - `reports/qa/stage8-live-rehearsal-20260306T152505Z.md`
  - `reports/qa/cycle-20260306T152504Z.md`
  - `reports/qa/stage8-live-rehearsal-20260306T164913Z.md` (QA worktree)
  - `reports/qa/cycle-20260306T164914Z.md` (QA worktree)

## Skip/Failure Reasons
- feature worktree에는 `fastapi`, `httpx` runtime dependency가 없어 incident runtime smoke와 live rehearsal이 실행되지 않았다.
- live rehearsal은 `NEWCLAW_STAGE8_LIVE_ENABLED`, `NEWCLAW_REDMINE_MCP_ENDPOINT`, sandbox metadata가 준비된 QA worktree에서 다시 실행해야 한다.
- QA worktree에서는 runtime smoke가 실제로 통과했지만, live flag와 endpoint가 없어 live rehearsal은 여전히 `SKIP`이다.
- 현재 실패 항목은 없다.

## Next Action
- feature worktree MWU gate는 닫혔으므로, 다음 단계는 QA worktree 재검증이다.
- QA worktree runtime 재검증은 완료됐다.
- 다음 단계는 sandbox credential과 live flag를 넣은 상태에서 `bash scripts/run_stage8_live_rehearsal.sh`를 `PASS`로 실행하는 것이다.
- 외부 sandbox credential이 준비되면 `PASS` 리포트로 교체하고 파일럿/Go-No-Go 패키지 작업으로 이동한다.
