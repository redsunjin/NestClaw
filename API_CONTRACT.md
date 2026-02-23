# API 계약서 초안 (v0.1)

## 1) 목적
로컬 업무 위임 오케스트레이션의 최소 API 계약을 고정한다.
범위는 `create/run/status` 3개 엔드포인트로 제한한다.

## 2) 공통 규칙
- Base Path: `/api/v1`
- Content-Type: `application/json`
- 시간 표기: ISO 8601 UTC (`YYYY-MM-DDTHH:mm:ssZ`)
- ID 형식: `task_<uuid>`
- 인증: 로컬 환경 기준 토큰 인증(구현체에서 선택)

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
- 운영 전환 시 DB 테이블(`tasks`, `task_events`, `task_runs`)로 분리 권장
