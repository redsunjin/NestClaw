# NestClaw Capability Manifest

## 1. 목적
- 이 문서는 현재 NestClaw가 상위 에이전트와 인간 운영자에게 어떤 capability를 제공하는지 한 장에서 보여주는 canonical manifest다.
- 현재 canonical machine-readable surface는 `GET /api/v1/capabilities`와 MCP `catalog.manifest`다.

## 2. Product Posture
- 제품 유형: local-first LLM job control plane + human approval/audit dashboard
- 기본 사용자: 로컬 LLM wrapper, 상위 대화형 에이전트, 운영 스크립트, approver/admin
- 기본 진입점: `agent.submit/status/events`
- 인간용 GUI 역할: 작업 생성 UI보다 상태/승인/감사 dashboard
- 별도 human interactive TUI: 비목표
- agent-facing non-interactive CLI: 핵심 표면
- cloud/API LLM: 조직 정책과 sensitivity routing 안에서 선택 가능한 provider

## 3. Workflow Families
| Family | 현재 상태 | 설명 |
| --- | --- | --- |
| `task` | `LLM planner baseline` | 자연어 요청을 받아 summary/ticket/slack 범위의 planner 루프를 수행 |
| `incident` | `AI planner + deterministic fallback` | incident context를 바탕으로 provider-backed planning을 시도하고, 실패 시 deterministic fallback으로 approval/execution/report 흐름을 유지 |

## 3.1 Stage 12 Candidate Concepts
| Concept | 목표 |
| --- | --- |
| `agent_profile` | 로컬 LLM 또는 cloud/API provider가 사용할 수 있는 job/capability/budget/sensitivity boundary 정의 |
| `job_template` | 반복 가능한 작업의 입력, capability, provider policy, output evidence 정의 |
| `capability_pack` | curated tool bundle을 job/profile에 연결 |
| `execution_budget` | max tool calls, retries, runtime, token/context 사용량 제한 |
| `schedule_trigger` | cron/launchd/CI/external scheduler가 호출할 수 있는 비대화형 실행 계약 |

Stage 12 roadmap:
- `NESTCLAW_AGENT_PROFILE_SPEC_2026-04-27.md`
- `configs/agent_profiles.json`
- `NESTCLAW_JOB_TEMPLATE_SPEC_2026-04-28.md`
- `configs/job_templates.json`
- `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md`
- `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`

## 4. Delivery Surfaces
| Surface | 현재 상태 | 주 용도 |
| --- | --- | --- |
| HTTP API | Stable baseline | 상위 서비스, web, scripted integration |
| Non-interactive CLI | Stable baseline | agent wrapper, 로컬 자동화, 운영 스크립트 |
| MCP Server | Stable baseline | 상위 대화형 에이전트 통합 |
| Web Quickstart `/` | Lightweight | 단일 실행/결과 확인 |
| Web Console `/console` | Operator dashboard | 상태/승인/카탈로그/드래프트 운영, 필요 시 보조 chat panel |

### 4.1 MCP Transport Boundary
- 현재 canonical transport: `stdio`
- 현재 상태: stable baseline
- remote gateway: future boundary
- actor context: `actor_id` 필수, `actor_role` 명시 권장
- 참조 문서: `NESTCLAW_MCP_TRANSPORT_DEPLOYMENT_GUIDE.md`

## 5. Execution Capabilities
### 5.1 현재 planner가 직접 다루는 tool set
- `internal.summary.generate`
- `redmine.issue.create`
- `slack.message.send`

### 5.2 현재 registry/capability surface가 다루는 범위
- tool catalog list/get
- tool draft create/get/validate/apply
- tool rollback
- execution metadata 조회

### 5.3 현재 live readiness 조건부 capability
- sandbox rehearsal
- live rehearsal
- Redmine MCP live bridge

비고:
- 위 live capability는 외부 env가 비어 있으면 `BLOCKED`다.

### 5.4 Provider Posture
- 현재 model registry는 local provider와 cloud/API provider를 모두 표현한다.
- local provider는 sensitive/internal 작업의 기본 경로다.
- cloud/API provider는 low sensitivity 또는 general reasoning 작업에서 정책적으로 허용될 수 있다.
- provider invocation provenance는 status/event/report 계층에 남겨야 한다.

## 6. Control Surface by Role
| Capability | requester | reviewer | approver | admin |
| --- | --- | --- | --- | --- |
| agent submit | yes | limited | limited | yes |
| agent status/events/report | own task | broad read | broad read | broad read |
| approval list/detail | no | limited by policy | yes | yes |
| approval approve/reject | no | no | yes | yes |
| tools list/get | yes | yes | yes | yes |
| tool draft create/get/validate | yes | yes | yes | yes |
| tool draft apply | no | no | yes | yes |
| tool rollback | no | no | yes | yes |

## 7. Auth Modes
- Local JWT
- External IdP JWT + JWKS
- Trusted SSO headers
- Compatibility actor headers

호환 헤더:
- `X-Actor-Id`
- `X-Actor-Role`

## 8. Observable Runtime Fields
상위 에이전트와 대시보드가 반드시 활용해야 하는 필드:
- `task_id`
- `resolved_kind`
- `status`
- `current_stage`
- `next_action`
- `approval_queue_id`
- `approval_reason`
- `planning_provenance`
- `planned_actions`
- `action_results`
- `provider_invocation`
- `report_path`

## 9. Current Known Constraints
- broader multi-step planning은 제한적이다.
- incident AI planner는 현재 ticket/slack 범위의 제한된 tool set에서만 동작한다.
- RAG/live provider는 readiness env에 의존한다.
- GUI는 operator-first 방향이지만 아직 일부 governance 기능이 같은 화면에 섞여 있다.
- agent profile, job template, capability pack은 아직 canonical runtime schema로 구현되지 않았다.
- schedule trigger는 현재 core scheduler가 아니라 external scheduler가 HTTP/CLI/MCP를 호출하는 방식으로만 열려 있다.

## 10. Integration Guidance
상위 에이전트는 이 manifest를 이렇게 사용한다.

1. 어떤 workflow family가 현재 안정적인지 판단
2. 어떤 role로 호출할지 결정
3. approval-required action을 자동으로 우회하지 않도록 guardrail 설정
4. live/sandbox capability를 env readiness와 함께 해석
5. planner 가능 범위를 넘는 요청은 사용자에게 명확히 제약 설명

## 11. Runtime Export Surface
- HTTP: `GET /api/v1/capabilities`
- HTTP: `GET /api/v1/agent/bundle/{task_id}`
- HTTP: `GET /api/v1/agent/handoff/{task_id}`
- MCP: `catalog.manifest`
- MCP: `agent.bundle`
- MCP: `agent.handoff`
- CLI: `newclaw capabilities --json`
- CLI: `newclaw bundle --task-id <task_id> --json`
- CLI: `newclaw handoff --task-id <task_id> --json`
