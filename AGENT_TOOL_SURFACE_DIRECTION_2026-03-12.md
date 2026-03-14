# Agent Tool Surface Direction (2026-03-12)

## 목적
현재 프로젝트를 "HTTP 중심 백엔드 PoC"에서 "AI가 기본 실행 경로를 담당하고, 사람/상위 에이전트/스크립트가 공통으로 호출하는 orchestration AI agent"로 고도화하기 위한 방향을 고정한다.

## 현재 냉정한 상태
- 현재 강점:
  - 단일 agent 진입점이 있다. (`POST /api/v1/agent/submit`, `GET /api/v1/agent/status/{task_id}`, `GET /api/v1/agent/events/{task_id}`)
  - 현재 구현된 workflow family(`task`, `incident`)를 한 요청 경로에서 분기할 수 있다.
  - 회의요약 보고서 생성과 incident dry-run orchestration이 동작한다.
  - 승인 큐, RBAC, audit, retry, persistence, QA gate가 이미 들어가 있다.
  - 비대화형 tool CLI가 있다. (`submit/status/events/approve/reject --json`)
  - MCP server가 있다. (`agent.submit/status/events`, `approval.*`)
  - model registry 기반 provider selection logging과 LLM intent classifier fallback 경로가 있다.
  - task workflow에는 LLM planner baseline이 들어갔고, task status/event에 `planning_provenance`, `eligible_tools`를 남긴다.
  - Redmine MCP live bridge 경로와 rehearsal script가 준비되어 있다.
- 현재 한계:
  - 현재 기본 runtime은 `task path AI-first baseline + broader fallback/transitional state`에 가깝다.
  - classifier는 `task` / `incident` 분기를 담당하고, task planner는 `summary/ticket/slack` 좁은 tool set까지만 다룬다.
  - tool registry / capability schema와 catalog 조회 표면은 생겼고 task planner가 일부 사용하지만, incident planner 공통화와 richer cross-action planning은 아직 없다.
  - summary workflow를 제외하면 model registry selection이 아직 provider invocation으로 넓게 이어지지 않는다.
  - RAG 어댑터는 여전히 dry-run 중심이다.
  - Stage 8 전체 readiness는 sandbox/live env 부재로 `7/8` 상태다.

## 지금 실제로 할 수 있는 일
1. agent 요청 하나로 일반 task 또는 incident workflow를 생성/실행할 수 있다.
2. 회의요약 입력을 받아 액션 아이템 보고서를 생성할 수 있다.
3. incident 입력을 받아 context 집계, action card 생성, 승인/실행, 보고서 흐름을 dry-run으로 재현할 수 있다.
4. 위험 액션은 승인 큐로 전환하고 승인/반려 이력을 추적할 수 있다.
5. 상태 조회, 이벤트 로그, 품질 게이트, rehearsal report를 반복 실행할 수 있다.

## 아직 못 하는 일
1. 자연어 요청만으로 LLM이 broader tool set을 계획하고 `incident`까지 공통 planner로 다루는 범용 agent 동작
2. 실제 live RAG를 통한 사내 지식/시스템 신호 기반 reasoning
3. tool registry / capability schema를 planner가 사용해 여러 도구를 단계적으로 선택하는 범용 agent 동작
4. 운영자가 쓰는 전용 GUI 콘솔

## 권장 구조
`코어 서비스 -> HTTP/CLI/MCP 공통 표면` 구조로 정리한다.

```text
Core Services
  - AgentService
  - TaskService
  - IncidentService
  - ApprovalService
  - ToolExecutionService

Delivery Surfaces
  - FastAPI
  - Non-interactive CLI
  - MCP Server
  - Minimal Operator UI (later)
```

핵심 원칙:
- 실제 orchestration 로직은 FastAPI handler 안에 남기지 않는다.
- CLI와 MCP는 HTTP wrapper가 아니라 같은 service 계층을 직접 호출해야 한다.
- 사람, 스크립트, AI가 같은 계약과 같은 audit trail을 공유해야 한다.

## CLI 방향
현재 menu CLI는 유지하되, 다음 단계의 기본은 비대화형 CLI다.

권장 명령:
- `newclaw submit --text "..." --kind auto --json`
- `newclaw status --task-id <id> --json`
- `newclaw events --task-id <id> --json`
- `newclaw approve --queue-id <id> --comment "..." --json`
- `newclaw reject --queue-id <id> --comment "..." --json`

CLI 원칙:
- 항상 `--json` 지원
- exit code 고정
- stdin/json 입력 지원
- 대화형 menu는 데모/로컬 운영 보조 경로로만 유지

## MCP 방향
MCP는 CLI를 감싸는 것이 아니라, 같은 코어 서비스를 tool로 노출한다.

권장 tool:
- `agent.submit`
- `agent.status`
- `agent.events`
- `approval.list`
- `approval.approve`
- `approval.reject`

MCP 원칙:
- 입력/출력은 구조화된 JSON
- tool 이름은 CLI 명령과 1:1 대응
- auth, approval, audit, idempotency는 HTTP/CLI와 동일 정책 사용

## 권장 실행 순서
1. incident planner 공통화와 richer sequencing
- 현재 task path에 들어간 `AI-first planner -> policy gate -> executor` baseline을 incident path와 richer sequencing으로 확장한다.

2. incident/provider/RAG 확장
- task/incident planning contract를 수렴하고, summary path에 한정된 provider invocation을 incident planning/reporting으로 넓힌다.

3. operator UI 정리
- planner provenance와 approval reasoning이 보이는 최소 운영 콘솔을 붙인다.

## 다음 MWU 후보
1. `agent-s9-tool-planning-loop`
- 목적: incident planner provenance와 task/incident action-card를 registry 기반 multi-step planner/executor 계약으로 수렴

2. `agent-s10-incident-provider-rag`
- 목적: incident planning/reporting의 provider invocation과 live retrieval을 확장

3. `agent-s11-operator-ui`
- 목적: planner provenance/approval reasoning 중심의 최소 operator UI 설계/구현

## 판단 기준
이 프로젝트가 OpenClaw류 agent에 가까워졌다고 볼 수 있는 기준은 아래다.
- 사람은 CLI나 UI로 같은 agent를 쓸 수 있다.
- 상위 UX나 상위 에이전트(rfs-cli 포함)는 NestClaw에 목표를 넘기고, 계획/도구 선택의 주체는 NestClaw다.
- 외부 AI는 MCP tool로 같은 agent를 호출할 수 있다.
- core service는 HTTP/CLI/MCP 중 어느 표면에도 종속되지 않는다.
- `auto` routing이 실제 모델 기반 intent + policy + tool planning으로 동작하고, heuristic/template은 degraded mode로만 남는다.
