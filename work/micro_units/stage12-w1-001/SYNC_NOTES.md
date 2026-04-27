# Sync Notes

## Release Actions
- Stage12 G1 Agent Profile baseline을 `NESTCLAW_AGENT_PROFILE_SPEC_2026-04-27.md`로 고정했다.
- `configs/agent_profiles.json`에 local LLM, cloud/API LLM, upper-agent wrapper, deterministic fallback 샘플 profile을 추가했다.
- Stage12를 `run_dev_qa_cycle.sh`와 `run_auto_cycle.sh`의 target range에 추가했다.
- dev/QA cycle에 `NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS` 기반 timeout runner를 추가해 dependency-gated checks가 무기한 멈추지 않도록 했다.
- README, local LLM control plane 문서, capability manifest, Stage12 work groups에서 Agent Profile 산출물을 연결했다.

## QA Sync Evidence
- `work/micro_units/stage12-w1-001/reports/plan-gate-20260427T145243Z.md`
- `work/micro_units/stage12-w1-001/reports/review-gate-20260427T145926Z.md`
- `work/micro_units/stage12-w1-001/reports/implement-gate-20260427T150635Z.md`
- `work/micro_units/stage12-w1-001/reports/evaluate-gate-20260427T150644Z.md`
- `reports/qa/cycle-20260427T150337Z.md`
- `reports/qa/cycle-20260427T150644Z.md`
- `reports/qa/cycle-20260427T150844Z.md`
- `python3 -m unittest tests.test_stage8_contract tests.test_stage9_contract tests.test_stage10_contract tests.test_stage11_contract tests.test_stage12_contract`
- `env PATH=../nestclaw-ideation-qa/.venv/bin:$PATH NEWCLAW_CYCLE_CHECK_TIMEOUT_SECONDS=15 NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 12`

## Final State
- `stage12-w1-001`은 local-first LLM job control plane의 첫 경계 객체인 Agent Profile을 문서/샘플/계약 테스트로 고정했다.
- cloud/API provider는 배제하지 않되, profile sensitivity boundary와 approval policy 안에서만 선택 가능한 경로로 표현했다.
- runtime validator는 아직 만들지 않았다. G2 Job Template과 G3 Capability Pack vocabularies가 안정된 뒤 validation/runtime binding을 추가하는 것이 맞다.
- 다음 item은 `g2-job-template-spec`다.
