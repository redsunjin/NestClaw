# Sync Notes

## Release Actions
- `newclaw job list` and `newclaw job describe` discovery surfaces added.
- Discovery payloads expose executable status, compatible profile ids, required capability packs, runtime surfaces, and examples.
- `stage12-w2-001` marked DONE.

## QA Sync Evidence
- Plan gate: `work/micro_units/stage12-w2-001/reports/plan-gate-20260427T160728Z.md`
- Review gate: `work/micro_units/stage12-w2-001/reports/review-gate-20260427T160729Z.md`
- Implement gate: `work/micro_units/stage12-w2-001/reports/implement-gate-20260427T160729Z.md`
- Evaluate gate: `work/micro_units/stage12-w2-001/reports/evaluate-gate-20260427T160748Z.md`
- Stage 12 cycle: `reports/qa/cycle-20260427T160748Z.md`
- Direct static: `python3 -m unittest tests.test_stage12_contract`
- Direct runtime: `python3 -m app.cli job list --json`
- Direct runtime: `python3 -m app.cli job describe --template readiness_check --profile local_ops_default --json`

## Final State
- DONE. Upper agents can discover job templates before invoking `job run`.
