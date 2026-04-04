# Evaluate Notes

## QA Result Summary
- 검증 명령:
  - `python3 -m unittest tests.test_stage8_contract tests.test_stage9_contract tests.test_planner_executor_service`
  - `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_planner_executor_service tests.test_stage9_contract tests.test_agent_planner_runtime tests.test_incident_runtime_smoke`
  - `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_stage8_self_eval.sh`
  - `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`
- 결과:
  - stage8/stage9/helper unittest: PASS (`49 tests`)
  - shared helper + runtime smoke: PASS (`20 tests`)
  - stage8 self evaluation: PASS (`7/8`, pending only sandbox CI evidence)
  - full QA cycle stage9: PASS (`pass: 58 / fail: 0 / skip: 4`)
- 확보된 리포트:
  - `reports/qa/stage8-self-eval-20260404T142232Z.md`
  - `reports/qa/cycle-20260404T142433Z.md`
  - `work/micro_units/stage9-w1-002/reports/plan-gate-20260404T141558Z.md`
  - `work/micro_units/stage9-w1-002/reports/review-gate-20260404T141914Z.md`
  - `work/micro_units/stage9-w1-002/reports/implement-gate-20260404T142433Z.md`
  - `work/micro_units/stage9-w1-002/reports/evaluate-gate-20260404T142433Z.md`
  - `work/micro_units/stage9-w1-002/reports/evaluate-cycle-20260404T142505Z.log`

## Skip/Failure Reasons
- 코드 회귀 실패는 없음
- env-gated skip:
  - browser swagger smoke: Playwright session unavailable (`newclaw-browser-smoke`)
  - postgres rehearsal: `NEWCLAW_DATABASE_URL` 미설정
  - stage8 sandbox rehearsal: `NEWCLAW_STAGE8_SANDBOX_ENABLED` 미설정
  - stage8 live rehearsal: `NEWCLAW_STAGE8_LIVE_ENABLED` 미설정
- stage8 self evaluation의 남은 pending은 sandbox rehearsal PASS evidence 부재이며, 현재 live/sandbox env blocker와 일치한다.

## Next Action
- `stage9-w1-002` implement/evaluate gate를 통과시키고 campaign item을 `completed`로 정리한다.
- 다음 단위에서는 `g2-incident-ai-reasoning` 범위, 즉 incident AI planner baseline과 deterministic fallback 수렴을 시작한다.
