# NestClaw Local LLM Job Control Plane Roadmap

## Roadmap Purpose
- NestClaw의 다음 제품 버전을 `local-first LLM job control plane`으로 구체화한다.
- 기존 `closed orchestration runtime + operator dashboard` 방향은 유지한다.
- 새 목표는 로컬 LLM이 승인된 job template과 capability pack 안에서 반복 작업을 안전하게 실행하도록 관리하는 것이다.
- cloud/API LLM은 local-first 원칙을 깨지 않는 선택 provider로 유지한다.

## Versioning Decision
- 기존 제품 문서를 폐기하지 않는다.
- `NESTCLAW_PRODUCT_POSITIONING.md`는 canonical definition을 v2 방향으로 갱신한다.
- 새 축은 `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE.md`와 이 roadmap 문서에 분리해서 관리한다.
- 실제 개발 단위는 `stage12-priority-campaign`으로 연동한다.

## Product Thesis
로컬 LLM은 범용 에이전트처럼 모든 도구와 컨텍스트를 직접 다루기 어렵다. NestClaw는 로컬 LLM에게 무제한 자율성을 주는 대신, 사람이 승인한 job, capability, budget, provider policy 안에서 일을 실행하게 만드는 관리 계층이 된다.

## Roadmap Principles
- Local-first: 내부 데이터와 반복 작업은 로컬 provider를 기본 경로로 둔다.
- Provider-optional: cloud/API provider는 sensitivity와 policy routing이 허용할 때만 쓴다.
- Job-oriented: agent persona가 아니라 반복 가능한 job template을 중심 단위로 둔다.
- Capability-scoped: LLM은 job에 연결된 capability pack만 쓴다.
- Evidence-first: 모든 실행은 status, events, report, audit, handoff packet으로 남긴다.
- Dashboard-as-operator: GUI는 관리/승인/감사/상태 확인용이며 main chat app이 아니다.

## Stage 12 Milestones
### M1. Agent Profile Baseline
- 목표: 로컬 LLM, 상위 agent, cloud/API provider를 같은 profile vocabulary로 표현한다.
- 산출물:
  - `NESTCLAW_AGENT_PROFILE_SPEC_2026-04-27.md`
  - sample profile registry 또는 schema draft
  - contract test
- 핵심 필드:
  - `profile_id`
  - `provider_id`
  - `provider_class`
  - `allowed_job_templates`
  - `allowed_capability_packs`
  - `execution_budget`
  - `sensitivity_boundary`
  - `approval_policy`
  - `audit_level`
- 완료 기준:
  - local provider와 cloud/API provider가 같은 schema로 표현된다.
  - sensitive/internal 작업은 local-first로 라우팅된다는 정책이 명시된다.

### M2. Job Template Baseline
- 목표: 반복 가능한 업무를 template으로 정의한다.
- 산출물:
  - `NESTCLAW_JOB_TEMPLATE_SPEC_2026-04-28.md`
  - `configs/job_templates.json`
  - 최소 sample job 3개
  - template validation smoke
- sample jobs:
  - `daily_status_digest`
  - `issue_triage`
  - `readiness_check`
- 완료 기준:
  - job template이 input schema, capability pack, provider policy, schedule trigger, output evidence를 포함한다.
  - 기존 `agent.submit/status/events/report`와 연결되는 실행 경로가 설명된다.

### M3. Capability Pack Binding
- 목표: curated tool registry를 job/profile에 연결한다.
- 산출물:
  - `NESTCLAW_CAPABILITY_PACK_SPEC_2026-04-28.md`
  - `configs/capability_packs.json`
  - approval requirements mapping
- 완료 기준:
  - pack이 allowed tools, denied tools, approval requirements, data boundary를 표현한다.
  - marketplace가 아니라 curated pack이라는 guardrail이 유지된다.

### M4. Execution Budget and Schedule Trigger
- 목표: 로컬 LLM의 context/tool overuse를 제한하고 외부 scheduler 호출 계약을 고정한다.
- 산출물:
  - budget fields in profile/job spec
  - `newclaw job run` 또는 equivalent non-interactive invocation plan
  - cron/launchd/CI 호출 예시
- 완료 기준:
  - max tool calls, max retries, max elapsed seconds, max provider tokens가 실행 전 policy로 해석된다.
  - schedule trigger는 core runtime을 우회하지 않고 `agent.submit` 또는 job run wrapper를 호출한다.

### M5. Local LLM Job Invocation PoC
- 목표: 로컬 LLM provider가 제한된 job 하나를 실행하고 evidence를 남기는 end-to-end PoC를 만든다.
- 산출물:
  - `newclaw job run` compatible CLI wrapper
  - `scripts/run_stage12_local_job_poc.sh`
  - `NESTCLAW_LOCAL_JOB_INVOCATION_POC_2026-04-28.md`
  - one runnable job template/profile/pack path: `daily_status_digest` + `local_ops_default` + `internal_digest_basic`
  - status/events/report/bundle/handoff evidence
- 완료 기준:
  - local provider가 기본 경로로 선택된다.
  - cloud/API provider는 low sensitivity 또는 explicit policy에서만 선택된다.
  - job 실행이 bundle/handoff에서 확인 가능하다.

### M6. External Scheduler Invocation
- 목표: cron, launchd, CI, 상위 agent가 Stage 12 job을 안전하게 반복 호출할 수 있는 표준 wrapper를 제공한다.
- 산출물:
  - `NESTCLAW_STAGE12_SCHEDULER_INVOCATION_GUIDE_2026-04-28.md`
  - `scripts/run_stage12_scheduled_job.sh`
  - `scripts/run_stage12_scheduler_smoke.sh`
  - `examples/stage12_scheduler/`
- 완료 기준:
  - scheduler wrapper가 `newclaw job run`과 `newclaw job history`를 모두 호출한다.
  - 실행 결과, history, input, summary 증적이 `reports/stage12-scheduled-runs/`에 남는다.
  - schedule trigger는 core runtime을 우회하지 않고 Stage 12 job surface를 호출한다.

### M7. Scheduled Job Idempotency
- 목표: 외부 scheduler가 같은 job을 반복 호출할 때 중복 실행 여부를 machine-readable하게 판단할 수 있게 한다.
- 산출물:
  - `idempotency_key` and `input_fingerprint` in `job.run`
  - same fields in `job.history`
  - `--duplicate-policy run|skip|fail` in `scripts/run_stage12_scheduled_job.sh`
  - `scripts/run_stage12_scheduler_dedupe_smoke.sh`
- 완료 기준:
  - 같은 idempotency key로 두 번째 호출 시 `skip` 정책이 새 job 실행 없이 `SKIPPED_DUPLICATE` 증적을 남긴다.
  - Stage 12 dev-QA cycle이 dedupe smoke를 포함한다.

### M8. LLM Harness Configuration Guide
- 목표: 로컬 LLM, cloud/API LLM, 상위 agent wrapper가 어떤 설정 경계를 통해 NestClaw job을 실행해야 하는지 표준화한다.
- 산출물:
  - `NESTCLAW_LLM_HARNESS_CONFIGURATION_GUIDE_2026-04-28.md`
  - `stage12-llm-harness-configuration-campaign`
- 완료 기준:
  - provider/profile/job/capability/invocation/QA harness의 책임이 명시된다.
  - 새 local LLM 추가 순서와 cloud/API provider 제한이 문서화된다.
  - contract tests가 guide와 campaign 존재를 확인한다.

## Stage 12 Priority Campaign
| Group | Item | Unit | Outcome |
| --- | --- | --- | --- |
| G1 | Agent Profile Spec | `stage12-w1-001` | local/cloud provider profile vocabulary |
| G2 | Job Template Spec | `stage12-w1-002` | repeatable job schema and samples |
| G3 | Capability Pack Binding | `stage12-w1-003` | curated pack to job/profile mapping |
| G4 | Local Job Invocation PoC | `stage12-w1-004` | constrained local LLM job execution evidence |

## Implementation Order
1. Spec first: agent profile, job template, capability pack.
2. Registry second: machine-readable sample configs.
3. Runtime third: validation and invocation surfaces.
4. Dashboard later: only after runtime payloads are stable.

## Stage 12 Follow-Up Campaign
`stage12-job-surface-campaign` extends the completed priority campaign with two practical surfaces:

- `stage12-w2-001`: `newclaw job list/describe` discovery for upper agents and operators.
- `stage12-w2-002`: `readiness_check` executable adapter using the same status/events/report/bundle/handoff evidence contract.

`stage12-agent-facing-job-api-campaign` exposes that same contract through service-native surfaces:

- `stage12-w3-001`: HTTP `GET /api/v1/jobs`, `GET /api/v1/jobs/{template_id}`, and `POST /api/v1/jobs/run`.
- `stage12-w3-002`: MCP `job.list`, `job.describe`, and `job.run`.

`stage12-job-execution-hardening-campaign` turns the service surface into more practical work execution:

- `stage12-w4-001`: `issue_triage` executable dry-run incident adapter plus budget guardrails before runtime submission.

`stage12-job-history-dashboard-campaign` makes executed jobs observable without adding a separate runtime:

- `stage12-w5-001`: `job.history`, `GET /api/v1/jobs/runs`, `newclaw job history`, and a read-only dashboard job-run panel.

`stage12-scheduler-invocation-campaign` makes those jobs callable by external schedulers without adding a second runtime:

- `stage12-w6-001`: scheduler-safe wrapper, cron/launchd/GitHub Actions examples, and Stage 12 cycle smoke coverage.

`stage12-scheduler-dedupe-campaign` adds safe repeat invocation semantics for external schedulers:

- `stage12-w7-001`: idempotency keys, input fingerprints, duplicate `run/skip/fail` policy, and dedupe smoke coverage.

`stage12-llm-harness-configuration-campaign` documents how LLMs are managed through the Stage 12 harness:

- `stage12-w8-001`: provider/profile/job/capability/invocation/QA harness guide for local and cloud LLM setup.

## UI/UX Position
- No large UI rewrite is required for Stage 12.
- Existing console can absorb new data as lists/details:
  - agent profiles
  - job templates
  - capability packs
  - scheduled runs
  - execution budgets
  - run history
- Quickstart may receive copy updates later, but should not become a main chat app.

## Cloud/API Provider Policy
- Cloud/API provider support remains open.
- Use cases:
  - low sensitivity summarization
  - template/spec review
  - high-quality reasoning over non-sensitive metadata
- Restrictions:
  - no automatic sensitive payload transfer
  - provenance required
  - external send still requires approval when policy says so

## Risks
- If the product is described as agent management, it may drift toward an agent hub.
- If cloud/API provider routing is too easy, local-first positioning becomes cosmetic.
- If job templates are too flexible, they recreate general-purpose agent complexity.
- If UI comes first, the runtime contract may stay vague.

## Near-Term Definition of Done
- Stage 12 campaign exists and all four MWUs are completed.
- Agent Profile spec is completed as `stage12-w1-001`.
- Job Template spec is completed as `stage12-w1-002`.
- Capability Pack spec is completed as `stage12-w1-003`.
- Local Job Invocation PoC is completed as `stage12-w1-004`.
- `newclaw job run` validates template/profile/capability pack boundaries before runtime submission.
- `newclaw job list/describe` exposes read-only discovery before invocation.
- `readiness_check` is executable through the same local-first job contract.
- `issue_triage` is executable through the same local-first job contract in incident dry-run mode.
- `newclaw job run` rejects budget overrides and timeout overruns before `agent.submit`.
- `newclaw job history`, MCP `job.history`, and HTTP `/api/v1/jobs/runs` expose completed and in-flight job evidence.
- `scripts/run_stage12_scheduled_job.sh` lets cron, launchd, CI, and upper agents invoke Stage 12 jobs while preserving job history evidence.
- Stage 12 job runs expose `idempotency_key` and `input_fingerprint` through run and history surfaces.
- `NESTCLAW_LLM_HARNESS_CONFIGURATION_GUIDE_2026-04-28.md` defines how providers, profiles, jobs, capability packs, invocation, and QA gates are configured together.
- Stage 12 cycle includes local job invocation smoke coverage.
- Stage 12 cycle includes scheduler invocation smoke coverage.
- Stage 12 cycle includes scheduler duplicate detection smoke coverage.
- Roadmap is linked from README and capability manifest.
- Existing Stage 9-11 tests still pass.
