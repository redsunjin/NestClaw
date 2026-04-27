# Evaluate Notes

## QA Result Summary
- `python3 -m json.tool configs/agent_profiles.json`: PASS.
- `python3 -m py_compile scripts/run_with_timeout.py`: PASS.
- `bash -n scripts/run_dev_qa_cycle.sh scripts/run_auto_cycle.sh`: PASS.
- `python3 -m unittest tests.test_stage12_contract`: PASS, 7 tests.
- `python3 -m unittest tests.test_stage8_contract tests.test_stage9_contract tests.test_stage10_contract tests.test_stage11_contract tests.test_stage12_contract`: PASS, 77 tests.
- `bash scripts/run_micro_cycle.sh gate-review stage12-w1-001`: PASS, report `work/micro_units/stage12-w1-001/reports/review-gate-20260427T145926Z.md`.
- `env PATH=../nestclaw-ideation-qa/.venv/bin:$PATH NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS=15 NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 12`: PASS, 66 pass, 0 fail, 5 skip, report `reports/qa/cycle-20260427T150337Z.md`.
- Final rerun after campaign sync: PASS, 66 pass, 0 fail, 5 skip, report `reports/qa/cycle-20260427T150844Z.md`.

## Skip/Failure Reasons
- No hard failures in the bounded Stage12 dev/QA cycle.
- Browser Swagger smoke skipped because the dependency-gated Playwright command exceeded the 15 second local verification timeout.
- Postgres rehearsal skipped because `NEWCLAW_DATABASE_URL` is not set.
- Stage8 grouped self-evaluation baseline was intentionally skipped with `NEWCLAW_SKIP_STAGE8_SELF_EVAL=1` to avoid nested full-cycle recursion during Stage12 harness verification.
- Stage8 sandbox/live rehearsals remain skipped because `NEWCLAW_STAGE8_SANDBOX_ENABLED` and `NEWCLAW_STAGE8_LIVE_ENABLED` are not enabled.

## Next Action
- Proceed to Stage12 G2: define the Job Template spec and sample jobs that bind to these Agent Profiles.
- Add runtime validation later after Job Template and Capability Pack vocabularies are stable.
