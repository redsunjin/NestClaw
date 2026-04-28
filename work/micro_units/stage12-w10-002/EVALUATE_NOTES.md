# Evaluate Notes

## QA Result Summary
- JSON parse for `configs/job_templates.json`: PASS.
- Direct production validator: PASS, `errors=0`, `warnings=5`.
- Direct negative fixture validator: expected FAIL, `errors=28`, `warnings=0`.
- Stage 12 contract tests: PASS, `21 tests`.
- Stage 12 job invocation smoke tests in QA venv: PASS, `8 tests`.
- Scheduler smoke in QA venv: PASS.
- Scheduler dedupe smoke in QA venv: PASS.
- Stage 12 dev-QA cycle in QA venv: PASS, `71 pass / 0 fail / 5 skip`, report `reports/qa/cycle-20260428T131413Z.md`.
- Micro evaluate gate: PASS, report `work/micro_units/stage12-w10-002/reports/evaluate-gate-20260428T131514Z.md`, cycle report `reports/qa/cycle-20260428T131514Z.md`.

## Skip/Failure Reasons
No expected new skip is introduced by this unit. The full Stage 12 cycle retains the existing 5 skips: browser swagger dependency timeout, PostgreSQL env gate, Stage 8 grouped self-eval intentionally skipped for nested cycle, Stage 8 sandbox disabled, and Stage 8 live disabled.

## Next Action
After this unit passes, continue with validator warning cleanup or first real local LLM provider onboarding.
