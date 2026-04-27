# Sync Notes

## Release Actions
- Stage12 G3 Capability Pack baseline을 `NESTCLAW_CAPABILITY_PACK_SPEC_2026-04-28.md`로 고정했다.
- `configs/capability_packs.json`에 Agent Profile과 Job Template에서 참조하는 모든 pack id를 추가했다.
- `configs/agent_profiles.json`의 `allowed_capability_packs`를 Job Template 요구 pack과 맞췄다.
- Stage12 contract tests에 profile-template-pack-tool cross-reference 검증을 추가했다.
- README, local LLM control plane 문서, capability manifest, roadmap, Stage12 work groups에서 Capability Pack 산출물을 연결했다.

## QA Sync Evidence
- `work/micro_units/stage12-w1-003/reports/plan-gate-20260427T152914Z.md`
- `work/micro_units/stage12-w1-003/reports/review-gate-20260427T152938Z.md`
- `work/micro_units/stage12-w1-003/reports/implement-gate-20260427T153145Z.md`
- `work/micro_units/stage12-w1-003/reports/evaluate-gate-20260427T153244Z.md`
- `reports/qa/cycle-20260427T153154Z.md`
- `reports/qa/cycle-20260427T153244Z.md`
- `reports/qa/cycle-20260427T153349Z.md`
- `python3 -m unittest tests.test_stage12_contract`
- `python3 -m unittest tests.test_stage8_contract tests.test_stage9_contract tests.test_stage10_contract tests.test_stage11_contract tests.test_stage12_contract`

## Final State
- `stage12-w1-003`은 capability pack을 LLM tool allowlist boundary로 고정했고, wildcard tool access를 금지했다.
- `ticket_draft_ops`는 Redmine write-capable tools를 참조하지만 dry-run/approver-gated policy로 제한된다.
- `core_status_readonly`와 `nestclaw_control_readonly`는 tool execution보다 runtime read surfaces를 명시하는 readonly pack으로 표현했다.
- 다음 item은 `g4-local-job-invocation-poc`다.
