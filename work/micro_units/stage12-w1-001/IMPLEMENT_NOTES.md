# Implement Notes

## Changed Files
- `NESTCLAW_AGENT_PROFILE_SPEC_2026-04-27.md`: defined the Stage 12 Agent Profile vocabulary, required fields, provider classes, budget rules, sensitivity boundary, approval policy, runtime invariants, and planned agent-facing surfaces.
- `configs/agent_profiles.json`: added local LLM, cloud/API LLM, upper-agent wrapper, and deterministic fallback sample profiles.
- `tests/test_stage12_contract.py`: added Stage12 contract coverage for the Agent Profile spec, sample registry, local-first sensitivity boundary, cloud/API approval boundary, and timeout-aware cycle harness.
- `scripts/run_dev_qa_cycle.sh`: expanded target range to Stage12, added `check_stage_12`, and wrapped checks with a configurable timeout.
- `scripts/run_auto_cycle.sh`: expanded target range to Stage12.
- `scripts/run_with_timeout.py`: added process-group timeout runner for dev/QA checks.
- `tests/test_stage8_contract.py`, `tests/test_stage9_contract.py`, `tests/test_stage10_contract.py`, `tests/test_stage11_contract.py`: updated cycle range assertions from `1..11` to `1..12`.
- `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE.md`, `NESTCLAW_CAPABILITY_MANIFEST.md`, `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`, `README.md`: linked the Agent Profile baseline artifacts.

## Rollback Plan
- Revert the Stage12 Agent Profile spec, sample registry, and Stage12 contract test additions together.
- Revert `scripts/run_dev_qa_cycle.sh` and `scripts/run_auto_cycle.sh` to the previous Stage11 target range if Stage12 is paused.
- Remove `scripts/run_with_timeout.py` only after removing the `run_check_command` calls from `scripts/run_dev_qa_cycle.sh`.

## Known Risks
- Timeout-based skip can hide slow optional dependency checks when `NEWCLAW_STRICT_GATE=0`; strict release gates should use `NEWCLAW_STRICT_GATE=1` and a production timeout value.
- `configs/agent_profiles.json` is a contract sample, not yet enforced by runtime validators.
- Job Template and Capability Pack specs are still pending, so profile references are intentionally forward-looking.
