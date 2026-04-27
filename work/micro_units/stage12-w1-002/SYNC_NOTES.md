# Sync Notes

## Release Actions
- Stage12 G2 Job Template baseline을 `NESTCLAW_JOB_TEMPLATE_SPEC_2026-04-28.md`로 고정했다.
- `configs/job_templates.json`에 `daily_status_digest`, `issue_triage`, `readiness_check` 샘플 job을 추가했다.
- `configs/agent_profiles.json`의 `allowed_job_templates`를 샘플 job과 맞춰 Agent Profile과 Job Template이 상호 참조되게 했다.
- Stage12 contract tests에 job template registry, profile reference, local-first provider policy, cloud/API optionality, schedule trigger, output evidence 검증을 추가했다.
- README, local LLM control plane 문서, capability manifest, roadmap, Stage12 work groups에서 Job Template 산출물을 연결했다.

## QA Sync Evidence
- `work/micro_units/stage12-w1-002/reports/plan-gate-20260427T151840Z.md`
- `work/micro_units/stage12-w1-002/reports/review-gate-20260427T151858Z.md`
- `work/micro_units/stage12-w1-002/reports/implement-gate-20260427T152039Z.md`
- `work/micro_units/stage12-w1-002/reports/evaluate-gate-20260427T152138Z.md`
- `reports/qa/cycle-20260427T152053Z.md`
- `reports/qa/cycle-20260427T152138Z.md`
- `reports/qa/cycle-20260427T152358Z.md`
- `python3 -m unittest tests.test_stage12_contract`
- `python3 -m unittest tests.test_stage8_contract tests.test_stage9_contract tests.test_stage10_contract tests.test_stage11_contract tests.test_stage12_contract`

## Final State
- `stage12-w1-002`은 repeatable job을 자유 프롬프트가 아니라 input schema, allowed profiles, capability pack references, provider policy, schedule trigger, output evidence가 있는 contract로 고정했다.
- Cloud/API provider는 `issue_triage`에서 redacted/low sensitivity + approval-required 조건으로만 열린다.
- Capability pack ids는 G3에서 canonical schema와 approval mapping으로 확정해야 한다.
- 다음 item은 `g3-capability-pack-binding`이다.
