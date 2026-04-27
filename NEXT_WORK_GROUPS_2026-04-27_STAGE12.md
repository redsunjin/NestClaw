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

## Recommended Order
1. G1 Agent Profile Spec
2. G2 Job Template Spec
3. G3 Capability Pack Binding
4. G4 Local LLM Job Invocation PoC

## Operating Track
- Stage 8 live readiness는 external env handoff가 들어오는 즉시 별도로 재실행한다.
- 최신 external env request kit:
  - `STAGE8_EXTERNAL_ENV_REQUEST_KIT_2026-04-10.md`

## Campaign Candidate
- `stage12-priority-campaign`
- Goal: turn NestClaw into a local-first LLM job control plane while preserving cloud/API provider optionality.
- Roadmap reference: `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md`
- Completed first unit: `stage12-w1-001`
- Completed second unit: `stage12-w1-002`
- Completed third unit: `stage12-w1-003`
- Completed fourth unit: `stage12-w1-004`
- Next focus: extend the job invocation adapter to another template or plan the next Stage 12 campaign.
