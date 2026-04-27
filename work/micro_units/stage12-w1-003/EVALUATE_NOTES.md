# Evaluate Notes

## QA Result Summary
- `python3 -c "import json, pathlib; [json.loads(pathlib.Path(p).read_text()) for p in ('configs/agent_profiles.json','configs/job_templates.json','configs/capability_packs.json','work/priority_campaigns/stage12-priority-campaign/campaign.json')]"`: PASS.
- `python3 -m unittest tests.test_stage12_contract`: PASS, 9 tests.
- `python3 -m unittest tests.test_stage8_contract tests.test_stage9_contract tests.test_stage10_contract tests.test_stage11_contract tests.test_stage12_contract`: PASS, 79 tests.
- `env PATH=../nestclaw-ideation-qa/.venv/bin:$PATH NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS=15 NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 12`: PASS, 66 pass, 0 fail, 5 skip, report `reports/qa/cycle-20260427T153154Z.md`.
- Evaluate gate rerun: PASS, report `work/micro_units/stage12-w1-003/reports/evaluate-gate-20260427T153244Z.md`, cycle report `reports/qa/cycle-20260427T153244Z.md`.
- Final bounded Stage12 cycle after sync: PASS, 66 pass, 0 fail, 5 skip, report `reports/qa/cycle-20260427T153349Z.md`.

## Skip/Failure Reasons
- No hard failures in the static contract checks or bounded Stage12 dev/QA cycle.
- Browser Swagger smoke skipped because the dependency-gated Playwright command exceeded the 15 second local verification timeout.
- Postgres rehearsal skipped because `NEWCLAW_DATABASE_URL` is not set.
- Stage8 grouped self-evaluation baseline was intentionally skipped with `NEWCLAW_SKIP_STAGE8_SELF_EVAL=1`.
- Stage8 sandbox/live rehearsals remain skipped because `NEWCLAW_STAGE8_SANDBOX_ENABLED` and `NEWCLAW_STAGE8_LIVE_ENABLED` are not enabled.

## Next Action
- Close G3 and move next to G4 Local LLM Job Invocation PoC.
