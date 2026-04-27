# NestClaw Local LLM Job Control Plane

## 1. Positioning
- NestClaw는 로컬 LLM과 상위 cloud/API LLM이 조직 내부 작업을 안전하게 실행하도록 관리하는 job-oriented orchestration control plane이다.
- 기본 우선순위는 `local-first`다.
- cloud/API LLM은 조직 정책이 허용하고 sensitivity가 낮거나 일반 reasoning 품질이 필요한 경우 선택 가능한 provider로 둔다.
- 핵심 제품 가치는 에이전트 자체를 전시하는 것이 아니라, LLM에게 맡길 수 있는 정해진 작업과 도구 실행을 안전하게 관리하는 데 있다.

## 2. Why This Direction Exists
- 로컬 LLM을 범용 에이전트처럼 직접 쓰면 context window, tool selection, memory, permission, retry, audit 문제가 빠르게 커진다.
- NestClaw는 로컬 LLM이 모든 판단과 도구 사용을 즉흥적으로 하게 두지 않고, 전문가/상위 agent가 설계한 job template과 capability pack 안에서 실행하게 만든다.
- 고성능 cloud/API agent는 job과 tool contract를 설계하거나 검토할 수 있고, 로컬 LLM은 내부망/보안/저비용 반복 실행에 집중할 수 있다.

## 3. Product Definition
- NestClaw는 `LLM에게 일을 시키는 안전한 작업 실행 관리자`다.
- 사람은 job, policy, approval, evidence를 관리한다.
- 로컬 LLM은 승인된 job template과 capability만 사용한다.
- cloud/API LLM은 provider registry와 policy routing 안에서 선택적으로 사용된다.

## 4. Primary Concepts
### Agent Profile
- 특정 로컬 LLM 또는 상위 agent가 어떤 job과 capability를 사용할 수 있는지 정의한다.
- Stage 12 baseline spec:
  - `NESTCLAW_AGENT_PROFILE_SPEC_2026-04-27.md`
  - `configs/agent_profiles.json`
- 포함 항목:
  - provider id
  - allowed job families
  - allowed capability packs
  - max tool calls
  - max runtime
  - context budget
  - approval policy
  - data sensitivity boundary

### Job Template
- 반복 가능한 정해진 작업을 정의한다.
- Stage 12 baseline spec:
  - `NESTCLAW_JOB_TEMPLATE_SPEC_2026-04-28.md`
  - `configs/job_templates.json`
- 예:
  - daily status digest
  - issue triage
  - meeting summary
  - incident dry-run
  - local document indexing
  - readiness check

### Capability Pack
- 전문가/상위 agent가 설계하고 검토한 tool 묶음이다.
- 공개 marketplace가 아니라 curated registry다.
- pack은 job template과 agent profile에 연결된다.
- Stage 12 baseline spec:
  - `NESTCLAW_CAPABILITY_PACK_SPEC_2026-04-28.md`
  - `configs/capability_packs.json`

### Schedule Trigger
- cron, launchd, CI, external scheduler가 NestClaw job을 비대화형으로 호출하는 진입점이다.
- NestClaw 자체는 execution contract와 audit를 보장하고, scheduler는 호출 타이밍을 담당한다.
- Stage 12 PoC surface:
  - `python3 -m app.cli job list --json`
  - `python3 -m app.cli job describe --template <template_id> --profile <profile_id> --json`
  - `newclaw job run`
  - `python3 -m app.cli job run --template daily_status_digest --profile local_ops_default --input-file <json> --json`
  - `python3 -m app.cli job run --template readiness_check --profile local_ops_default --input-file <json> --json`
  - HTTP: `GET /api/v1/jobs`, `GET /api/v1/jobs/{template_id}`, `POST /api/v1/jobs/run`
  - MCP: `job.list`, `job.describe`, `job.run`
  - `scripts/run_stage12_local_job_poc.sh`

### Execution Budget
- 로컬 LLM의 과도한 tool use와 context 낭비를 막는 실행 제한이다.
- 예:
  - max tool calls
  - max retries
  - max elapsed seconds
  - max provider tokens
  - human approval required on external send

## 5. Provider Policy
| Provider Class | 기본 용도 | 정책 |
| --- | --- | --- |
| local LLM | 내부 데이터, 반복 작업, 저비용 실행 | 기본 경로 |
| cloud/API LLM | 낮은 민감도, 고품질 reasoning, 설계/검토 | policy routing으로 허용 |
| deterministic fallback | provider 실패 또는 비활성 | degraded mode |

## 6. Guardrails
- 로컬 LLM이 직접 무제한 tool registry를 탐색하지 않게 한다.
- cloud/API LLM에는 민감 데이터가 자동 전달되지 않게 한다.
- job template 밖의 action은 approval 또는 rejection으로 분류한다.
- tool draft/apply는 기존 review/approval/audit를 유지한다.
- dashboard chat이나 future chat surface는 기존 submit/status/report를 감싸는 보조면으로만 둔다.

## 7. Non-Goals
- agent marketplace
- persona agent collection
- 사람용 main chat 업무 앱
- local LLM을 unrestricted general-purpose agent로 만드는 것
- cloud/API LLM 의존형 SaaS agent hub

## 8. Stage 12 Candidate Scope
1. `Agent Profile` spec
2. `Job Template` spec
3. `Capability Pack` spec
4. non-interactive scheduled job invocation contract
5. one local LLM PoC job using existing CLI/MCP/HTTP surfaces

Detailed roadmap:
- `NESTCLAW_AGENT_PROFILE_SPEC_2026-04-27.md`
- `NESTCLAW_JOB_TEMPLATE_SPEC_2026-04-28.md`
- `NESTCLAW_CAPABILITY_PACK_SPEC_2026-04-28.md`
- `NESTCLAW_LOCAL_JOB_INVOCATION_POC_2026-04-28.md`
- `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md`
- `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`
- `work/priority_campaigns/stage12-priority-campaign/campaign.json`

## 9. Success Criteria
- 로컬 LLM 하나가 승인된 job template 하나를 제한된 capability pack으로 실행한다.
- 실행 결과가 status/events/report/audit로 남는다.
- provider routing이 local-first 원칙을 따른다.
- cloud/API provider는 명시된 policy 조건에서만 사용된다.
- 사람은 dashboard에서 상태, 승인, 실패/blocked 이유를 확인할 수 있다.
