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
- 확보된 리포트:
  - `work/micro_units/stage8-w5-001/reports/plan-gate-20260306T152504Z.md`
  - `work/micro_units/stage8-w5-001/reports/review-gate-20260306T152504Z.md`
  - `work/micro_units/stage8-w5-001/reports/implement-gate-20260306T152504Z.md`
  - `work/micro_units/stage8-w5-001/reports/evaluate-gate-20260306T152504Z.md`
  - `work/micro_units/stage8-w5-001/reports/evaluate-cycle-20260306T152505Z.log`
  - `reports/qa/stage8-live-rehearsal-20260306T152505Z.md`
  - `reports/qa/cycle-20260306T152504Z.md`

## Skip/Failure Reasons
- feature worktree에는 `fastapi`, `httpx` runtime dependency가 없어 incident runtime smoke와 live rehearsal이 실행되지 않았다.
- live rehearsal은 `NEWCLAW_STAGE8_LIVE_ENABLED`, `NEWCLAW_REDMINE_MCP_ENDPOINT`, sandbox metadata가 준비된 QA worktree에서 다시 실행해야 한다.
- 현재 실패 항목은 없다.

## Next Action
- feature worktree MWU gate는 닫혔으므로, 다음 단계는 QA worktree 재검증이다.
- QA worktree를 최신 커밋으로 fast-forward 한 뒤, runtime dependency가 있는 환경에서 `bash scripts/run_stage8_live_rehearsal.sh`를 재실행한다.
- 외부 sandbox credential이 준비되면 `PASS` 리포트로 교체하고 파일럿/Go-No-Go 패키지 작업으로 이동한다.
