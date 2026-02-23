# 승인 큐 데이터 모델 초안 (v0.1)

## 1) 목적
`NEEDS_HUMAN_APPROVAL` 상태 작업을 일관되게 처리하기 위한 데이터 모델을 정의한다.

## 2) 엔티티 개요
- `approval_queue`: 승인 대기 항목
- `approval_actions`: 승인/반려 이력

## 3) approval_queue 스키마
| 필드 | 타입 | 설명 |
|---|---|---|
| queue_id | string | `aq_<uuid>` |
| task_id | string | 연관 Task ID |
| request_id | string | 요청 추적 ID |
| reason_code | string | 승인 필요 사유 코드 |
| reason_message | string | 사용자 표시 메시지 |
| requested_by | string | 요청자 ID |
| approver_group | string | 승인 담당 그룹 |
| status | string | `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED` |
| created_at | datetime | 생성 시각 |
| expires_at | datetime | 만료 시각 |
| resolved_at | datetime/null | 처리 완료 시각 |

## 4) approval_actions 스키마
| 필드 | 타입 | 설명 |
|---|---|---|
| action_id | string | `aa_<uuid>` |
| queue_id | string | approval_queue 참조 |
| task_id | string | 연관 Task ID |
| action | string | `APPROVE`, `REJECT` |
| acted_by | string | 처리자 ID |
| comment | string | 처리 코멘트 |
| created_at | datetime | 처리 시각 |

## 5) 상태 전이
- `PENDING -> APPROVED`
- `PENDING -> REJECTED`
- `PENDING -> EXPIRED`

연계 규칙:
- `APPROVED`: Task 상태를 `RUNNING`으로 복귀
- `REJECTED`: Task 상태를 `DONE`으로 종료(반려 사유 기록)
- `EXPIRED`: Task 상태를 `DONE` 또는 정책별 후속 처리

## 6) 최소 API 초안
## 6.1 GET `/api/v1/approvals`
- 목적: 승인 대기 목록 조회
- 쿼리: `status=PENDING`, `approver_group=ops_team`

## 6.2 POST `/api/v1/approvals/{queue_id}/approve`
- 목적: 승인 처리 후 Task 재개
- 요청:
```json
{
  "acted_by": "approver_01",
  "comment": "업무 목적 확인됨"
}
```

## 6.3 POST `/api/v1/approvals/{queue_id}/reject`
- 목적: 반려 처리 후 Task 종료
- 요청:
```json
{
  "acted_by": "approver_01",
  "comment": "외부 전송 정책 위반"
}
```

## 7) 감사 로그 요구사항
- 승인 큐 생성/처리/만료 이벤트는 모두 로그로 남긴다.
- 로그 항목:
  - `queue_id`, `task_id`, `actor`, `action`, `reason_code`, `timestamp`

## 8) 운영 규칙
- 승인 없는 재실행 금지
- 동일 queue_id 중복 처리 금지(멱등 처리)
- 반려 시 재요청은 신규 queue_id로 생성
