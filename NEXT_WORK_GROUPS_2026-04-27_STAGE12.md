# Next Work Groups (2026-04-27, Stage 12)

## Purpose
Stage 11 campaign이 pilot operationalization을 닫은 뒤, NestClaw의 다음 제품 축을 `local-first LLM job control plane`으로 고정한다.

## Current Judgment
- NestClaw는 이미 HTTP / CLI / MCP / approval / audit / capability manifest / operator dashboard baseline을 갖고 있다.
- 로컬 LLM을 범용 에이전트처럼 직접 쓰는 방식은 context, tool selection, memory, permission, audit 비용이 크다.
- 따라서 다음 단계는 새 agent persona를 늘리는 것이 아니라, 로컬 LLM이 승인된 job과 capability만 실행하도록 관리하는 spec과 최소 PoC를 만드는 것이다.
- cloud/API LLM은 배제하지 않고, model registry와 policy routing 안에서 선택 가능한 provider로 유지한다.

## Groups
### G1. Agent Profile Spec
- Goal: provider, role, allowed jobs, allowed capability packs, budget, sensitivity boundary를 정의한다.
- Current artifact:
  - `NESTCLAW_AGENT_PROFILE_SPEC_2026-04-27.md`
  - `configs/agent_profiles.json`
- Done when:
  - agent profile 문서 또는 schema가 존재한다.
  - local provider와 cloud/API provider가 같은 profile vocabulary로 표현된다.
  - approval/audit boundary가 명시된다.

### G2. Job Template Spec
- Goal: 반복 가능한 작업 단위를 입력, capability, provider policy, schedule trigger, output evidence로 정의한다.
- Current artifact:
  - `NESTCLAW_JOB_TEMPLATE_SPEC_2026-04-28.md`
  - `configs/job_templates.json`
- Done when:
  - job template 문서 또는 schema가 존재한다.
  - 최소 3개 sample job이 정의된다.
  - template이 기존 `agent.submit/status/events/report`와 연결된다.

### G3. Capability Pack Binding
- Goal: curated capability registry를 job/profile과 연결한다.
- Current artifact:
  - `NESTCLAW_CAPABILITY_PACK_SPEC_2026-04-28.md`
  - `configs/capability_packs.json`
- Done when:
  - capability pack spec이 존재한다.
  - pack이 allowed tools와 approval requirements를 표현한다.
  - marketplace가 아니라 curated pack임을 guardrail로 고정한다.

### G4. Local LLM Job Invocation PoC
- Goal: local LLM provider가 job template 하나를 제한된 capability pack으로 실행하고 evidence를 남기는 최소 흐름을 구현한다.
- Current artifact:
  - `NESTCLAW_LOCAL_JOB_INVOCATION_POC_2026-04-28.md`
  - `scripts/run_stage12_local_job_poc.sh`
  - `tests/test_stage12_job_invocation_smoke.py`
- Done when:
  - non-interactive CLI 또는 MCP flow로 PoC job을 실행할 수 있다.
  - execution budget과 provider routing이 기록된다.
  - status/events/report/bundle/handoff에 trace가 남는다.

### G5. Scheduler Invocation Wrapper
- Goal: cron, launchd, CI, 상위 agent가 Stage 12 job을 외부에서 반복 호출하되 core runtime과 job guardrail을 우회하지 않게 한다.
- Current artifact:
  - `NESTCLAW_STAGE12_SCHEDULER_INVOCATION_GUIDE_2026-04-28.md`
  - `scripts/run_stage12_scheduled_job.sh`
  - `scripts/run_stage12_scheduler_smoke.sh`
  - `examples/stage12_scheduler/`
- Done when:
  - wrapper가 `job run` 이후 `job history`로 실행 흔적을 검증한다.
  - cron, launchd, GitHub Actions 예제가 같은 wrapper를 호출한다.
  - Stage 12 dev-QA cycle이 scheduler smoke를 포함한다.

### G6. Scheduled Job Dedupe
- Goal: 외부 scheduler가 같은 job을 반복 호출할 때 idempotency key로 중복 실행을 감지하고 정책적으로 run/skip/fail을 선택한다.
- Current artifact:
  - `scripts/run_stage12_scheduler_dedupe_smoke.sh`
  - `stage12-scheduler-dedupe-campaign`
- Done when:
  - `job.run`과 `job.history`가 `idempotency_key`, `input_fingerprint`를 노출한다.
  - scheduler wrapper가 `--duplicate-policy run|skip|fail`을 지원한다.
  - Stage 12 dev-QA cycle이 dedupe smoke를 포함한다.

### G7. LLM Harness Configuration
- Goal: 로컬 LLM, cloud/API LLM, 상위 agent wrapper를 provider/profile/job/capability/invocation/QA harness로 설정하는 표준 절차를 고정한다.
- Current artifact:
  - `NESTCLAW_LLM_HARNESS_CONFIGURATION_GUIDE_2026-04-28.md`
  - `stage12-llm-harness-configuration-campaign`
- Done when:
  - 새 local LLM 추가 순서가 명시된다.
  - cloud/API provider 제한과 sensitivity boundary가 명시된다.
  - contract tests가 guide와 campaign을 확인한다.

### G8. LLM Harness Policy Validator
- Goal: 하네스 설정 기준을 실행 가능한 validator로 만들어 registry drift를 차단한다.
- Current artifact:
  - `scripts/validate_stage12_llm_harness.py`
  - `stage12-llm-harness-validator-campaign`
- Done when:
  - validator가 model/profile/job/capability registry를 교차 검증한다.
  - Stage 12 dev-QA cycle이 validator를 required check로 실행한다.
  - contract tests가 validator와 campaign을 확인한다.

### G9. LLM Harness Negative Validator Fixtures
- Goal: validator가 정상 경로뿐 아니라 local/cloud boundary, sensitivity, mutual allowlist, scheduler idempotency, capability pack policy 위반을 실제로 FAIL 처리하는지 고정한다.
- Current artifact:
  - `tests/fixtures/stage12_llm_harness_negative/`
  - `stage12-llm-harness-negative-fixtures-campaign`
- Done when:
  - negative fixture가 provider/profile/job/capability/model registry 위반을 포함한다.
  - contract tests가 validator CLI의 non-zero exit와 FAIL payload를 확인한다.
  - Stage 12 dev-QA cycle이 negative fixture 회귀를 포함한다.

### G10. Job Template Idempotency Examples
- Goal: job template마다 external scheduler와 upper agent가 복사해서 쓸 수 있는 concrete idempotency key format, example, duplicate policy를 고정한다.
- Current artifact:
  - `configs/job_templates.json`
  - `examples/stage12_scheduler/idempotency-policy.md`
  - `stage12-job-idempotency-examples-campaign`
- Done when:
  - `daily_status_digest`, `issue_triage`, `readiness_check` 모두 `idempotency_key_policy`를 가진다.
  - validator가 scheduled job의 key format, examples, recommended duplicate policy를 검증한다.
  - scheduler examples가 concrete `stage12:` key와 duplicate policy를 사용한다.

### G11. LLM Harness Warning Cleanup
- Goal: production harness registry가 warning 없이 strict validator를 통과하도록 미래 placeholder 참조와 비상호 pack-template 참조를 제거한다.
- Current artifact:
  - `scripts/validate_stage12_llm_harness.py --strict-warnings`
  - `stage12-llm-harness-warning-cleanup-campaign`
- Done when:
  - production validator 결과가 `errors=0`, `warnings=0`이다.
  - Stage 12 dev-QA cycle이 validator를 `--strict-warnings`로 실행한다.
  - 미래 job/pack 후보는 production allowlist가 아니라 별도 roadmap으로만 남긴다.

### G12. Local LLM Provider Onboarding
- Goal: 실제 local provider를 production profile로 승격하고, upper agent/scheduler가 같은 job 계약으로 호출할 수 있는 onboarding smoke를 제공한다.
- Current artifact:
  - `NESTCLAW_LOCAL_LLM_PROVIDER_ONBOARDING_GUIDE_2026-04-29.md`
  - `scripts/run_stage12_local_llm_onboarding_smoke.sh`
  - `stage12-local-llm-provider-onboarding-campaign`
- Done when:
  - `local_ollama_ops` profile이 `local_primary` Ollama provider에 연결된다.
  - `daily_status_digest`, `issue_triage`, `readiness_check`가 `local_ollama_ops`와 호환된다.
  - Stage 12 dev-QA cycle이 local LLM onboarding smoke를 포함한다.

### G13. Dashboard Harness Visibility
- Goal: operator dashboard가 Stage 12 harness 상태를 read-only로 확인할 수 있게 한다.
- Current artifact:
  - `GET /api/v1/llm-harness`
  - `app/static/agent-console.html`
  - `stage12-dashboard-harness-visibility-campaign`
- Done when:
  - dashboard가 strict validator status, profile/job/pack/provider counts, local onboarding profile을 보여준다.
  - endpoint가 production harness registry를 read-only payload로 반환한다.
  - web console runtime tests가 HTML/JS/CSS와 endpoint를 검증한다.

## Recommended Order
1. G1 Agent Profile Spec
2. G2 Job Template Spec
3. G3 Capability Pack Binding
4. G4 Local LLM Job Invocation PoC
5. G5 Scheduler Invocation Wrapper
6. G6 Scheduled Job Dedupe
7. G7 LLM Harness Configuration
8. G8 LLM Harness Policy Validator
9. G9 LLM Harness Negative Validator Fixtures
10. G10 Job Template Idempotency Examples
11. G11 LLM Harness Warning Cleanup
12. G12 Local LLM Provider Onboarding
13. G13 Dashboard Harness Visibility

## Operating Track
- Stage 8 live readiness는 external env handoff가 들어오는 즉시 별도로 재실행한다.
- 최신 external env request kit:
  - `STAGE8_EXTERNAL_ENV_REQUEST_KIT_2026-04-10.md`

## Campaign Candidate
- `stage12-priority-campaign`
- Goal: turn NestClaw into a local-first LLM job control plane while preserving cloud/API provider optionality.
- Follow-up campaign: `stage12-job-surface-campaign`
- Follow-up goal: expose job discovery surfaces and extend executable local-first job adapters.
- Agent-facing API campaign: `stage12-agent-facing-job-api-campaign`
- Agent-facing API goal: expose Stage 12 job discovery and invocation through HTTP and MCP.
- Execution hardening campaign: `stage12-job-execution-hardening-campaign`
- Execution hardening goal: promote issue triage to a dry-run executable job and enforce budget guardrails before runtime submission.
- Job history/dashboard campaign: `stage12-job-history-dashboard-campaign`
- Job history/dashboard goal: expose Stage 12 job run history to upper agents and the operator dashboard.
- Scheduler invocation campaign: `stage12-scheduler-invocation-campaign`
- Scheduler invocation goal: let external schedulers invoke bounded Stage 12 jobs and verify run history evidence.
- Scheduler dedupe campaign: `stage12-scheduler-dedupe-campaign`
- Scheduler dedupe goal: add idempotency keys, input fingerprints, and duplicate run/skip/fail policy.
- LLM harness configuration campaign: `stage12-llm-harness-configuration-campaign`
- LLM harness configuration goal: define how local/cloud LLMs are configured through provider/profile/job/capability/invocation/QA harness layers.
- LLM harness validator campaign: `stage12-llm-harness-validator-campaign`
- LLM harness validator goal: enforce harness policy as a required Stage 12 QA gate.
- LLM harness negative fixtures campaign: `stage12-llm-harness-negative-fixtures-campaign`
- LLM harness negative fixtures goal: prove the validator rejects broken local/cloud/sensitivity/allowlist/idempotency policy fixtures.
- Job idempotency examples campaign: `stage12-job-idempotency-examples-campaign`
- Job idempotency examples goal: pin concrete template-level idempotency keys and duplicate policies for scheduler and upper-agent callers.
- LLM harness warning cleanup campaign: `stage12-llm-harness-warning-cleanup-campaign`
- LLM harness warning cleanup goal: require zero-warning production harness validation in Stage 12 QA.
- Local LLM provider onboarding campaign: `stage12-local-llm-provider-onboarding-campaign`
- Local LLM provider onboarding goal: promote Ollama as a concrete local provider profile and prove bounded job invocation through the onboarding smoke.
- Dashboard harness visibility campaign: `stage12-dashboard-harness-visibility-campaign`
- Dashboard harness visibility goal: expose read-only Stage 12 harness status in the operator dashboard.
- Roadmap reference: `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md`
- Completed first unit: `stage12-w1-001`
- Completed second unit: `stage12-w1-002`
- Completed third unit: `stage12-w1-003`
- Completed fourth unit: `stage12-w1-004`
- Completed agent-facing API units: `stage12-w3-001`, `stage12-w3-002`
- Completed execution hardening unit: `stage12-w4-001`
- Completed job history/dashboard unit: `stage12-w5-001`
- Completed scheduler invocation unit: `stage12-w6-001`
- Completed scheduler dedupe unit: `stage12-w7-001`
- Completed LLM harness configuration unit: `stage12-w8-001`
- Completed LLM harness validator unit: `stage12-w9-001`
- Completed LLM harness negative fixture unit: `stage12-w10-001`
- Completed job idempotency examples unit: `stage12-w10-002`
- Completed LLM harness warning cleanup unit: `stage12-w10-003`
- Completed local LLM provider onboarding unit: `stage12-w11-001`
- Completed dashboard harness visibility unit: `stage12-w11-002`
- Current focus: final Stage 12 release readiness pass and branch sync.
