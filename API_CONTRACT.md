# API 계약서 초안 (v0.1)

## 1) 목적
로컬 업무 위임 오케스트레이션의 최소 API 계약을 고정한다.
사용자 진입점은 `agent submit/status/events`를 기본으로 하고, 하위 호환을 위해 `task/*`, `incident/*` 직접 엔드포인트를 유지한다.
현재 v0.1 구현 범위의 workflow family는 `task`와 `incident`이며, broader execution agent의 추가 tool/workflow family는 후속 단계에서 확장한다.
목표 제품은 `AI-first orchestration agent`이며, heuristic/template fallback은 운영 연속성을 위한 `degraded mode`로만 유지한다.

## 2) 공통 규칙
- Base Path: `/api/v1`
- Content-Type: `application/json`
- 시간 표기: ISO 8601 UTC (`YYYY-MM-DDTHH:mm:ssZ`)
- ID 형식: `task_<uuid>`
- 인증: JWT/SSO + 호환 헤더 방식
  - 권장:
    - `Authorization: Bearer <jwt>`
    - JWT claim: `sub`, `role`
  - 외부 IdP 토큰:
    - `X-SSO-Token: <jwt>`
    - 검증 기준: `NEWCLAW_IDP_JWKS_PATH`, `NEWCLAW_IDP_ISSUER`, `NEWCLAW_IDP_AUDIENCE`
  - 선택형 신뢰 SSO 헤더:
    - `X-SSO-User`
    - `X-SSO-Role`
    - 활성화: `NEWCLAW_ALLOW_TRUSTED_SSO_HEADERS=1`
  - 호환(개발/이관용):
    - `X-Actor-Id`
    - `X-Actor-Role`
    - 활성화: `NEWCLAW_ALLOW_COMPAT_HEADERS=1`

## 3) 데이터 모델
### 3.1 Task
```json
{
  "task_id": "task_2e85a6c5-6f8a-4f22-8c84-6d8dc3062b7b",
  "title": "회의요약 생성",
  "template_type": "meeting_summary",
  "status": "READY",
  "created_at": "2026-02-22T07:10:00Z",
  "updated_at": "2026-02-22T07:10:00Z"
}
```

### 3.2 상태 코드
- `READY`
- `RUNNING`
- `FAILED_RETRYABLE`
- `NEEDS_HUMAN_APPROVAL`
- `DONE`

### 3.3 표준 오류 응답
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "template_type is required",
    "request_id": "req_abc123"
  }
}
```

## 4) 엔드포인트 계약
## 4.1 POST `/api/v1/task/create`
작업을 생성하고 `READY` 상태로 반환한다.

권한:
- 허용 role: `requester`, `admin`
- `requester`는 `X-Actor-Id == requested_by` 조건 필요

요청:
```json
{
  "title": "회의요약 생성",
  "template_type": "meeting_summary",
  "input": {
    "meeting_title": "주간 운영회의",
    "meeting_date": "2026-02-22",
    "participants": ["Kim", "Lee"],
    "notes": "원문 메모..."
  },
  "requested_by": "user_01"
}
```

응답 `201 Created`:
```json
{
  "task_id": "task_2e85a6c5-6f8a-4f22-8c84-6d8dc3062b7b",
  "status": "READY",
  "created_at": "2026-02-22T07:10:00Z"
}
```

오류:
- `400 INVALID_REQUEST`
- `403 POLICY_DENIED`
- `409 DUPLICATE_REQUEST`

## 4.2 POST `/api/v1/task/run`
`READY` 상태 작업을 실행한다.
동일 Task에 대해 실행 요청이 중복될 수 있으므로 멱등성 키를 권장한다.

권한:
- 허용 role: `requester`, `admin`
- `requester`는 본인 Task만 실행 가능

요청:
```json
{
  "task_id": "task_2e85a6c5-6f8a-4f22-8c84-6d8dc3062b7b",
  "idempotency_key": "run_20260222_001",
  "run_mode": "standard"
}
```

응답 `202 Accepted`:
```json
{
  "task_id": "task_2e85a6c5-6f8a-4f22-8c84-6d8dc3062b7b",
  "status": "RUNNING",
  "started_at": "2026-02-22T07:11:00Z"
}
```

오류:
- `404 TASK_NOT_FOUND`
- `409 INVALID_TASK_STATE`
- `423 APPROVAL_REQUIRED`

## 4.3 GET `/api/v1/task/status/{task_id}`
현재 상태와 최신 실행 결과를 조회한다.

권한:
- 허용 role: `requester`, `reviewer`, `approver`, `admin`
- `requester`는 본인 Task만 조회 가능

응답 `200 OK` (진행 중):
```json
{
  "task_id": "task_2e85a6c5-6f8a-4f22-8c84-6d8dc3062b7b",
  "status": "RUNNING",
  "current_stage": "executor",
  "last_event_at": "2026-02-22T07:11:20Z",
  "next_action": "wait_for_completion"
}
```

응답 `200 OK` (완료):
```json
{
  "task_id": "task_2e85a6c5-6f8a-4f22-8c84-6d8dc3062b7b",
  "status": "DONE",
  "result": {
    "report_path": "reports/task_2e85a6c5/report.md"
  },
  "completed_at": "2026-02-22T07:12:10Z"
}
```

응답 `200 OK` (승인 필요):
```json
{
  "task_id": "task_2e85a6c5-6f8a-4f22-8c84-6d8dc3062b7b",
  "status": "NEEDS_HUMAN_APPROVAL",
  "approval_reason": "external_send_requested",
  "next_action": "approve_or_reject"
}
```

오류:
- `404 TASK_NOT_FOUND`

## 4.4 GET `/api/v1/task/events/{task_id}`
Task 이벤트 로그를 조회한다.

권한:
- 허용 role: `requester`, `reviewer`, `approver`, `admin`
- `requester`는 본인 Task만 조회 가능

응답:
```json
{
  "task_id": "task_...",
  "count": 4,
  "items": [
    {"event_type": "TASK_CREATED", "...": "..."}
  ]
}
```

## 4.5 GET `/api/v1/approvals`
승인 큐 목록을 조회한다.

권한:
- 허용 role: `approver`, `admin`

## 4.6 GET `/api/v1/approvals/{queue_id}`
승인 항목 상세와 action/comment history를 조회한다.

권한:
- 허용 role: `approver`, `admin`

응답:
```json
{
  "queue_id": "aq_...",
  "item": {
    "queue_id": "aq_...",
    "task_id": "task_...",
    "status": "PENDING",
    "reason_code": "external_send_requested"
  },
  "task_summary": {
    "task_id": "task_...",
    "title": "외부전송 테스트",
    "status": "NEEDS_HUMAN_APPROVAL"
  },
  "actions": [
    {
      "action": "APPROVE",
      "acted_by": "qa_approver",
      "comment": "approved in web console"
    }
  ],
  "action_count": 1
}
```

## 4.7 POST `/api/v1/approvals/{queue_id}/approve`
승인 처리 후 Task를 `RUNNING`으로 복귀시킨다.

권한:
- 허용 role: `approver`, `admin`

## 4.8 POST `/api/v1/approvals/{queue_id}/reject`
반려 처리 후 Task를 종료한다.

권한:
- 허용 role: `approver`, `admin`

## 4.9 GET `/api/v1/audit/summary`
감사 지표 요약을 조회한다.

권한:
- 허용 role: `reviewer`, `admin`

응답:
```json
{
  "total_events": 12,
  "blocked_policy_events": 2,
  "policy_bypass_events": 0,
  "approvals_pending": 1,
  "approvals_resolved": 3
}
```

## 4.10 POST `/api/v1/agent/submit`
단일 요청 진입점이다. 현재 v0.1에서는 `task` 또는 `incident` workflow family로 라우팅하고 기본값으로 즉시 실행한다.

권한:
- 허용 role: `requester`, `admin`
- `requester`는 `X-Actor-Id == requested_by` 조건 필요

요청:
```json
{
  "task_kind": "auto",
  "title": "주간 운영회의 요약",
  "request_text": "회의 메모를 요약하고 액션 아이템을 정리해줘",
  "requested_by": "user_01",
  "metadata": {
    "meeting_title": "주간 운영회의",
    "meeting_date": "2026-03-11",
    "participants": ["Kim", "Lee"]
  },
  "auto_run": true,
  "incident_run_mode": "dry-run"
}
```

응답 `202 Accepted`:
```json
{
  "task_id": "task_2e85a6c5-6f8a-4f22-8c84-6d8dc3062b7b",
  "entrypoint": "agent",
  "resolved_kind": "task",
  "status": "RUNNING",
  "created_at": "2026-03-11T03:00:00+00:00",
  "started_at": "2026-03-11T03:00:01+00:00",
  "auto_run": true
}
```

## 4.11 GET `/api/v1/agent/recent`
최근 agent task 히스토리를 조회한다. requester는 자신의 task만 보며, reviewer/approver/admin은 전체 최근 task를 볼 수 있다.

권한:
- 허용 role: `requester`, `reviewer`, `approver`, `admin`

쿼리:
- `limit` (기본 `10`, 최대 `50`)

응답:
```json
{
  "items": [
    {
      "task_id": "task_...",
      "title": "주간 운영회의 요약",
      "requested_by": "qa_user",
      "status": "DONE",
      "resolved_kind": "task",
      "updated_at": "2026-03-13T09:20:00+00:00",
      "approval_queue_id": null
    }
  ],
  "count": 1,
  "limit": 10
}
```

## 4.12 GET `/api/v1/agent/report/{task_id}`
task 또는 incident 결과 보고서의 preview를 조회한다. 접근 권한은 `agent_status`와 동일하다.

권한:
- 허용 role: `requester`, `reviewer`, `approver`, `admin`

쿼리:
- `max_chars` (기본 `4000`, 최소 `200`, 최대 `20000`)

응답:
```json
{
  "task_id": "task_...",
  "resolved_kind": "task",
  "status": "DONE",
  "report_path": "reports/task_xxx/report.md",
  "report_name": "report.md",
  "preview_text": "# 회의 요약\n...",
  "preview_chars": 4000,
  "truncated": false,
  "raw_url": "/api/v1/agent/report/task_xxx/raw"
}
```

## 4.13 GET `/api/v1/agent/report/{task_id}/raw`
보고서 markdown 원문을 파일 응답으로 내려준다. 접근 권한은 `agent_status`와 동일하다.

비고:
- `task_kind=auto`는 현재 LLM intent classifier + heuristic fallback으로 분류한다.
- `task` workflow는 현재 LLM planner baseline을 사용하고, 허용 tool set은 `internal.summary.generate`, `slack.message.send`다.
- execution tool catalog는 `configs/tool_registry.yaml` 기반으로 조회 가능하고, broader planner / execution adapter 일반화는 후속 단계 범위다.
- `meeting_summary`는 provider selection 이후 실제 provider invocation을 시도하고, 실패 시 템플릿 renderer로 fallback 한다.

## 4.10 GET `/api/v1/agent/status/{task_id}`
workflow 종류를 몰라도 단일 경로로 상태를 조회한다.

응답:
```json
{
  "task_id": "task_...",
  "entrypoint": "agent",
  "resolved_kind": "task",
  "status": "RUNNING",
  "current_stage": "executor",
  "last_event_at": "2026-03-11T03:00:04+00:00",
  "next_action": "wait_for_completion",
  "planning_provenance": {
    "source": "llm",
    "degraded_mode": false
  },
  "planned_actions": [
    {
      "tool_id": "internal.summary.generate"
    }
  ],
  "provider_invocation": {
    "result_source": "template_fallback",
    "fallback_reason": "live_summary_disabled"
  }
}
```

## 4.11 GET `/api/v1/agent/events/{task_id}`
workflow 종류를 몰라도 단일 경로로 이벤트 로그를 조회한다.

응답:
```json
{
  "task_id": "task_...",
  "entrypoint": "agent",
  "resolved_kind": "incident",
  "count": 5,
  "items": [
    {"event_type": "AGENT_ROUTED", "...": "..."}
  ]
}
```

## 4.12 GET `/api/v1/tools`
현재 등록된 execution tool catalog를 조회한다.

권한:
- 허용 role: `requester`, `approver`, `reviewer`, `admin`

응답:
```json
{
  "count": 7,
  "items": [
    {
      "tool_id": "redmine.issue.create",
      "title": "Create Redmine incident issue",
      "external_system": "redmine",
      "capability_family": "ticketing",
      "method": "issue.create"
    }
  ]
}
```

## 4.13 GET `/api/v1/tools/{tool_id}`
하나의 execution tool capability 상세를 조회한다.

응답:
```json
{
  "tool_id": "redmine.issue.create",
  "adapter": "redmine_mcp",
  "method": "issue.create",
  "action_type": "redmine_issue_create",
  "supports_dry_run": true,
  "required_payload_fields": ["project_id", "subject", "description", "priority"]
}
```

## 4.14 POST `/api/v1/tool-drafts`
새 도구를 production registry에 바로 반영하지 않고, reviewable draft로 생성한다.

권한:
- 허용 role: `requester`, `approver`, `reviewer`, `admin`

요청:
```json
{
  "requested_by": "qa_user",
  "request_text": "Slack 알림 도구를 추가하고 싶다"
}
```

응답:
```json
{
  "draft_id": "tooldraft_ab12cd34ef",
  "status": "DRAFT_REVIEW_REQUIRED",
  "path": "work/tool_drafts/tooldraft_ab12cd34ef.yaml",
  "tool": {
    "tool_id": "slack.messaging.custom",
    "adapter": "slack_api",
    "method": "message.send",
    "external_system": "slack"
  }
}
```

## 4.15 GET `/api/v1/tool-drafts/{draft_id}`
생성된 tool registration draft 내용을 조회한다.

응답:
```json
{
  "draft_id": "tooldraft_ab12cd34ef",
  "path": "work/tool_drafts/tooldraft_ab12cd34ef.yaml",
  "content": "draft_id: ..."
}
```

## 4.16 POST `/api/v1/tool-drafts/{draft_id}/apply`
approver/admin이 review한 draft를 overlay registry에 반영한다.
source registry(`configs/tool_registry.yaml`)는 직접 수정하지 않는다.

권한:
- 허용 role: `approver`, `admin`

요청:
```json
{
  "acted_by": "qa_approver"
}
```

응답:
```json
{
  "draft_id": "tooldraft_ab12cd34ef",
  "status": "APPLIED",
  "applied_by": "qa_approver",
  "tool": {
    "tool_id": "slack.message.ops_broadcast",
    "adapter": "slack_api",
    "method": "message.send"
  },
  "path": "work/tool_drafts/tooldraft_ab12cd34ef.yaml"
}
```

## 5) 이벤트 로깅 최소 스키마
```json
{
  "event_id": "evt_001",
  "task_id": "task_2e85a6c5-6f8a-4f22-8c84-6d8dc3062b7b",
  "event_type": "STATUS_CHANGED",
  "from_status": "READY",
  "to_status": "RUNNING",
  "actor": "system_orchestrator",
  "created_at": "2026-02-22T07:11:00Z"
}
```

## 6) 비기능 요구사항 (최소)
- 모든 상태 변경은 이벤트 로그를 남긴다.
- `task_id` 기반으로 전 구간 추적이 가능해야 한다.
- `NEEDS_HUMAN_APPROVAL` 상태에서는 자동 진행하지 않는다.

## 7) 구현 메모
- 초기 구현은 in-memory 저장소로 시작 가능
- 현재 구현: SQLite/PostgreSQL 영속 저장소 지원
  - SQLite: `NEWCLAW_DB_BACKEND=sqlite`, `NEWCLAW_DB_PATH` (기본 `data/new_claw.db`)
  - PostgreSQL: `NEWCLAW_DB_BACKEND=postgres`, `NEWCLAW_DATABASE_URL`
- 저장 테이블:
  - `tasks`
  - `events`
  - `approvals`
  - `approval_actions`
  - `run_idempotency`
- PostgreSQL 마이그레이션:
  - `migrations/postgres/001_init.sql`
  - `scripts/migrate_postgres.sh`
