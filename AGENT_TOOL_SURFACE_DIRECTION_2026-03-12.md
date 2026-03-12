# Agent Tool Surface Direction (2026-03-12)

## 목적
현재 프로젝트를 "HTTP 중심 백엔드 PoC"에서 "AI/운영자/스크립트가 공통으로 사용할 수 있는 오케스트레이션 에이전트"로 고도화하기 위한 방향을 고정한다.

## 현재 냉정한 상태
- 현재 강점:
  - 단일 agent 진입점이 있다. (`POST /api/v1/agent/submit`, `GET /api/v1/agent/status/{task_id}`, `GET /api/v1/agent/events/{task_id}`)
  - 일반 task와 incident workflow를 한 요청 경로에서 분기할 수 있다.
  - 회의요약 보고서 생성과 incident dry-run orchestration이 동작한다.
  - 승인 큐, RBAC, audit, retry, persistence, QA gate가 이미 들어가 있다.
  - 비대화형 tool CLI가 있다. (`submit/status/events/approve/reject --json`)
  - MCP server가 있다. (`agent.submit/status/events`, `approval.*`)
  - model registry 기반 provider selection logging과 LLM intent classifier fallback 경로가 있다.
  - Redmine MCP live bridge 경로와 rehearsal script가 준비되어 있다.
- 현재 한계:
  - classifier는 `task` / `incident` 분기까지만 담당하고, 실제 tool planning은 아직 없다.
  - model registry selection이 실제 provider invocation으로 이어지지 않는다.
  - RAG 어댑터는 여전히 dry-run 중심이다.
  - Stage 8 전체 readiness는 sandbox/live env 부재로 `7/8` 상태다.

## 지금 실제로 할 수 있는 일
1. agent 요청 하나로 일반 task 또는 incident workflow를 생성/실행할 수 있다.
2. 회의요약 입력을 받아 액션 아이템 보고서를 생성할 수 있다.
3. incident 입력을 받아 context 집계, action card 생성, 승인/실행, 보고서 흐름을 dry-run으로 재현할 수 있다.
4. 위험 액션은 승인 큐로 전환하고 승인/반려 이력을 추적할 수 있다.
5. 상태 조회, 이벤트 로그, 품질 게이트, rehearsal report를 반복 실행할 수 있다.

## 아직 못 하는 일
1. 자연어 요청만으로 LLM이 의도를 분류하고 tool을 스스로 고르는 범용 agent 동작
2. 실제 live RAG를 통한 사내 지식/시스템 신호 기반 reasoning
3. tool planning / execution card를 공통 루프로 돌리는 범용 agent 동작
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
1. 모델 라우팅 실제 연결
- `configs/model_registry.yaml` selection을 실제 provider invocation으로 이어 붙인다.

2. action-card / tool planning 공통 루프 정리
- 현재 task/incident 분기 뒤의 실행 단계를 공통 planner/executor 계약으로 수렴시킨다.

3. live RAG adapter 고도화
- dry-run evidence를 실제 retrieval/provider 호출로 바꾼다.

4. operator UI 추가
- 마지막 단계로 최소 운영 콘솔을 붙인다.

## 다음 MWU 후보
1. `agent-s6-provider-invocation`
- 목적: model registry selection을 실제 provider adapter 호출로 연결

2. `agent-s7-tool-planning-loop`
- 목적: task/incident action-card를 공통 planner/executor 계약으로 수렴

3. `agent-s8-live-rag`
- 목적: retrieval / signals adapter를 dry-run에서 실제 live 호출로 확장

4. `agent-s9-operator-ui`
- 목적: 최소 operator UI 설계/구현

## 판단 기준
이 프로젝트가 OpenClaw류 agent에 가까워졌다고 볼 수 있는 기준은 아래다.
- 사람은 CLI나 UI로 같은 agent를 쓸 수 있다.
- 외부 AI는 MCP tool로 같은 agent를 호출할 수 있다.
- core service는 HTTP/CLI/MCP 중 어느 표면에도 종속되지 않는다.
- `auto` routing이 실제 모델 기반 intent + policy + tool planning으로 동작한다.
