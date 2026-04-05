# NestClaw Agent Integration Spec

## 1. 목적
- 이 문서는 NestClaw를 "상위 대화형 에이전트가 호출하는 orchestration backend"로 붙일 때 필요한 통합 규칙을 고정한다.
- 대상 호출자는 Claude 같은 상위 대화형 에이전트, 로컬 스크립트, CLI wrapper, MCP client다.
- 인간은 직접 작업을 수행하는 주체라기보다 승인, 감사, 운영 판단을 담당하는 supervisor로 본다.

## 2. 제품 정의
- NestClaw의 1차 역할은 자연어 요청을 받아 workflow family를 분기하고, 정책/승인/감사/보고를 포함한 실행 루프를 닫는 것이다.
- NestClaw의 2차 역할은 인간 운영자가 현재 상태와 승인 필요 지점을 확인하는 dashboard를 제공하는 것이다.
- 별도의 인간용 interactive TUI는 product 목표로 두지 않는다.
- 대신 다른 terminal/agent/client가 HTTP, CLI, MCP를 통해 같은 orchestration runtime에 접근하게 한다.
- 따라서 상위 agent UX와 NestClaw GUI는 경쟁 관계가 아니라 계층 관계다.

권장 계층:

```text
User
  -> Upper Conversational Agent (Claude, Codex, internal chat agent)
    -> NestClaw (planning / policy / approval / audit / execution)
      -> Slack / Redmine / internal summary / future tools

Human Operator
  -> NestClaw Dashboard (/console)
```

보조 원칙:
- 사람을 위한 별도 TUI보다 에이전트를 위한 비대화형 CLI가 더 중요하다.
- dashboard 안에 chat panel을 둘 수는 있지만, 이는 operator dashboard의 보조 입력면이지 주 인터페이스가 아니다.

## 3. 책임 분리
### 3.1 상위 에이전트 책임
- 사용자의 목표를 수집하고 필요한 최소 metadata를 정리한다.
- NestClaw에 `agent.submit` 또는 HTTP/CLI 동등 진입점으로 요청을 제출한다.
- 상태를 polling하거나 이벤트를 읽는다.
- `NEEDS_HUMAN_APPROVAL`이면 사람 또는 적절한 권한 주체로 handoff한다.
- 완료 후 report preview/raw를 읽어 사용자에게 최종 응답을 구성한다.

### 3.2 NestClaw 책임
- `task` / `incident` 분기
- planner provenance 기록
- policy gate 적용
- approval queue 전환
- audit/event trail 유지
- tool execution dispatch
- result report 생성

### 3.3 인간 운영자 책임
- 고위험 승인/반려
- tool draft apply/rollback
- live mode 허용 여부 판단
- blocked env 해소

## 4. 권장 진입점
우선순위는 아래 순서다.

1. MCP
2. HTTP API
3. Non-interactive CLI
4. Web dashboard

해석:
- 상위 대화형 에이전트는 MCP를 기본으로 쓴다.
- MCP가 없거나 제한될 때 HTTP를 쓴다.
- 로컬 스크립트/배치/운영자는 CLI를 쓴다.
- 인간은 dashboard로 확인/승인/감사를 한다.
- 별도 human-oriented interactive TUI는 만들지 않는다.

## 5. Canonical Execution Loop
### 5.1 기본 루프
1. `submit`
2. `status`
3. `events`
4. session 시작 시 또는 capability 확인이 필요할 때 `capabilities`
5. 필요 시 `approvals`
6. `report`
7. handoff/export가 필요하면 `bundle`

### 5.2 권장 상태 해석
- `READY`: 생성은 됐지만 아직 실행 전이다.
- `RUNNING`: planner/executor/reviewer/reporter 중 하나가 진행 중이다.
- `FAILED_RETRYABLE`: 내부 재시도 또는 상위 재호출 판단이 필요하다.
- `NEEDS_HUMAN_APPROVAL`: 상위 에이전트는 자동 완료로 간주하면 안 된다.
- `DONE`: report를 읽고 사용자 응답을 마무리한다.

### 5.3 권장 next action 매핑
- `wait_for_completion`: polling 유지
- `approve_or_reject`: human handoff
- `open_report`: report preview/raw 조회
- `retry_allowed`: 상위 orchestration에서 재시도 정책 검토

위 `next_action` 값은 현재 payload 관측 결과를 기준으로 해석한 권장 통합 규칙이다.

## 6. 현재 표준 표면
### 6.1 HTTP
- `POST /api/v1/agent/submit`
- `GET /api/v1/agent/status/{task_id}`
- `GET /api/v1/agent/events/{task_id}`
- `GET /api/v1/agent/recent`
- `GET /api/v1/agent/report/{task_id}`
- `GET /api/v1/agent/report/{task_id}/raw`
- `GET /api/v1/agent/bundle/{task_id}`
- `GET /api/v1/capabilities`
- `GET /api/v1/approvals`
- `GET /api/v1/approvals/{queue_id}`
- `POST /api/v1/approvals/{queue_id}/approve`
- `POST /api/v1/approvals/{queue_id}/reject`
- `GET /api/v1/tools`
- `GET /api/v1/tools/{tool_id}`
- `POST /api/v1/tool-drafts`
- `GET /api/v1/tool-drafts/{draft_id}`
- `GET /api/v1/tool-drafts/{draft_id}/validate`
- `POST /api/v1/tool-drafts/{draft_id}/apply`
- `POST /api/v1/tools/{tool_id}/rollback`

### 6.2 CLI
- `newclaw submit`
- `newclaw status`
- `newclaw events`
 - `newclaw recent`
 - `newclaw report`
 - `newclaw bundle`
 - `newclaw approvals`
 - `newclaw approval-get`
- `newclaw approve`
- `newclaw reject`
- `newclaw tools`
- `newclaw capabilities`
- `newclaw tool-draft`
- `newclaw tool-validate`
- `newclaw tool-apply`
- `newclaw tool-rollback`

### 6.3 MCP
- `agent.submit`
- `agent.status`
- `agent.events`
 - `agent.recent`
 - `agent.report`
 - `agent.bundle`
- `approval.list`
 - `approval.get`
- `approval.approve`
- `approval.reject`
- `catalog.list`
- `catalog.get`
- `catalog.manifest`
- `catalog.create_draft`
- `catalog.get_draft`
- `catalog.validate_draft`
- `catalog.apply_draft`
- `catalog.rollback_tool`

### 6.4 MCP Transport Baseline
- 현재 canonical transport는 `stdio`다.
- 기준 실행 명령:
  - `python3 app/mcp_server.py`
- 상위 agent host는 이 프로세스를 child process로 띄우고 JSON-RPC over stdio로 연결하는 것을 기본으로 본다.
- `actor_id`는 모든 tool call에 포함하는 것이 권장된다.
- `actor_role`도 명시적으로 넣는 편이 좋고, 기본은 `requester` 또는 `reviewer`로 둔다.
- `approval.approve`, `approval.reject`, `catalog.apply_draft`, `catalog.rollback_tool`은 approver/admin boundary 안에서만 사용한다.
- packaged remote transport는 아직 baseline이 아니다. 필요한 경우 별도 wrapper/gateway에서 auth termination과 actor injection을 담당해야 한다.
- 상세 운영 가이드는 `NESTCLAW_MCP_TRANSPORT_DEPLOYMENT_GUIDE.md`를 기준으로 본다.

## 7. Role and Control Policy
### 7.1 기본 역할
- `requester`
- `reviewer`
- `approver`
- `admin`

### 7.2 상위 에이전트 권장 기본 role
- 기본은 `requester`
- review-only 관측 자동화는 `reviewer`
- approval 자동화는 기본 비권장
- `approver` / `admin`은 인간 proxy가 명시적으로 맡을 때만 사용

### 7.3 상위 에이전트가 해도 되는 일
- submit
- status/events/recent/report 조회
- tools/catalog 조회
- tool draft 생성 및 validate
- approval 필요 상태를 사람에게 전달

### 7.4 상위 에이전트가 기본적으로 하면 안 되는 일
- 사람 승인 없이 `approve` / `reject`
- 사람 승인 없이 `tool-draft apply`
- 사람 승인 없이 `tool rollback`
- 운영 기준이 없는 `live` 실행

## 8. Polling and Observability Policy
- `submit` 직후에는 `status`를 먼저 본다.
- `RUNNING`이면 `events`로 provenance와 action progress를 본다.
- polling 간격은 2~5초 수준의 저빈도 polling이 적절하다.
- 완료 판단은 상위 agent의 추론이 아니라 `status == DONE` 또는 `NEEDS_HUMAN_APPROVAL`로 한다.
- planner/source/tool choice 설명은 `planning_provenance`, `planned_actions`, `action_results`에서 읽는다.

## 9. Report Completion Policy
- 사용자는 NestClaw의 완료가 아니라 report가 생성된 시점의 업무 결과를 받는다.
- 따라서 상위 에이전트는 `DONE` 이후 아래 순서를 따른다.
1. `agent.report` preview 확인
2. 필요 시 raw markdown 조회
3. operator handoff나 audit export가 필요하면 `agent.bundle` 조회
4. preview/raw 또는 bundle에 근거해 최종 사용자 응답 생성

금지:
- status만 보고 결과를 상상해 응답
- approval pending인데 완료처럼 응답
- planner intent만 보고 execution 결과를 생략

## 10. Error / Blocked Handling
### 10.1 승인 대기
- `NEEDS_HUMAN_APPROVAL`이면 human approval queue id를 사용자 또는 운영자에게 전달한다.
- 상위 에이전트는 이 상태를 "진행 중"이 아니라 "인간 승인 대기"로 번역해야 한다.

### 10.2 degraded mode
- planner/provider가 degraded mode로 내려가도 contract는 유지된다.
- 상위 에이전트는 degraded mode를 숨기기보다 provenance로 노출하는 편이 낫다.

### 10.3 env blocked
- sandbox/live readiness는 env 부재 시 `BLOCKED`가 될 수 있다.
- 이는 기능 오류라기보다 운영 환경 미준비다.

### 10.4 Canonical Reason Vocabulary
- runtime과 readiness는 가능한 한 `canonical_state`와 `canonical_reason_code`를 같이 본다.
- 예:
  - `env_blocked`
  - `policy_blocked`
  - `approval_pending`
  - `retryable_failure`
  - `planner_degraded`
- 상위 에이전트는 이 reason code를 사용자 번역이나 handoff 판단의 기준으로 쓸 수 있다.

## 11. 권장 상위 에이전트 시스템 지침
상위 agent에 아래 운영 지침을 주는 것을 권장한다.

- NestClaw는 실행 backend이며, 네가 결과를 추정해 대체하면 안 된다.
- 작업 완료 여부는 항상 NestClaw status/report로 확인한다.
- 승인 필요 상태는 자동 완료로 처리하지 않는다.
- 고위험 제어면(`approve`, `apply_draft`, `rollback`, `live`)은 명시적 인간 승인 없이 호출하지 않는다.
- tool selection과 planner reasoning은 NestClaw가 담당하며, 상위 agent는 고수준 목표와 필요한 metadata만 넘긴다.

## 12. 현재 한계
- broader multi-tool planner는 아직 제한적이다.
- `incident`는 공통 관측 계약을 공유하지만 planner 자체는 deterministic/dry-run 중심이다.
- live external env가 없으면 readiness는 `BLOCKED`다.
- dashboard는 operator-first 방향이 맞지만, 아직 일부 governance surface가 과도하게 노출돼 있다.

## 13. 이 문서를 읽은 뒤 바로 구현해야 하는 것
1. MCP client에서 `agent.submit/status/events` 루프 구현
2. approval handoff UX 연결
3. report preview 또는 bundle 기반 최종 응답 생성
4. capability manifest를 startup 시 읽고 agent prompt에 반영
