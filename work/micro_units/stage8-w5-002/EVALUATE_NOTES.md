# Evaluate Notes

## QA Result Summary
- 검증 명령:
  - `env PYTHONPYCACHEPREFIX=.pycache python3 -m py_compile app/main.py app/cli.py tests/test_spec_contract.py tests/test_stage8_contract.py tests/test_agent_entrypoint_smoke.py`
  - `bash -n scripts/run_dev_qa_cycle.sh`
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `python3 -m unittest tests.test_agent_entrypoint_smoke tests.test_incident_runtime_smoke`
  - `env NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 8`
- QA worktree 검증 명령:
  - `env PATH="$PWD/.venv/bin:$PATH" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-qa-runtime.db bash scripts/run_dev_qa_cycle.sh 8`
- 결과:
  - 정적 compile/shell syntax: PASS
  - contract tests: PASS (`26 tests`)
  - agent + incident runtime smoke: SKIP (`9 skipped`, feature worktree runtime dependency 부재)
  - feature worktree stage 8 dev qa cycle: PASS (`reports/qa/cycle-20260311T131800Z.md`)
  - feature worktree micro cycle: PASS (`work/micro_units/stage8-w5-002/reports/evaluate-gate-20260311T131800Z.md`)
  - QA worktree stage 8 dev qa cycle: PASS (`reports/qa/cycle-20260311T131543Z.md`)
  - QA worktree browser smoke: PASS (QA 서버를 최신 커밋으로 재시작 후 통과)
  - QA worktree stage 8 self-eval baseline: PASS (`G1~G4 PASS`, `reports/qa/stage8-self-eval-20260311T131552Z.md`)

## Skip/Failure Reasons
- feature worktree에는 `fastapi`/`httpx` runtime stack이 없어 `tests.test_agent_entrypoint_smoke`, `tests.test_incident_runtime_smoke`가 skip 처리됐다.
- `run_dev_qa_cycle.sh 8`에서도 같은 이유로 runtime smoke는 optional skip으로 판정됐다.
- sandbox/live rehearsal은 env flag 미설정으로 계속 `SKIP`이다.
- QA worktree에서 직접 `python3 -m unittest ...`를 sandbox 제한 상태로 실행하면 `reports/<task_id>/` 쓰기 권한 때문에 false negative가 날 수 있다. canonical gate는 `bash scripts/run_dev_qa_cycle.sh 8` 기준으로 사용한다.

## Next Action
- `stage8-w5-002`는 완료로 닫고, 다음 단위는 facade 위에 실제 planner/LLM/tool selection을 붙이는 작업으로 넘어간다.
- 우선순위는 `rule-based router -> LLM intent router`, `agent facade -> approval/tool loop`, `API/CLI facade -> 최소 operator UI` 순서가 적절하다.
