# Task 상태 전이 문서 (v0.1)

## 1) 목적
`create/run/status` API가 공유하는 Task 상태 전이를 고정한다.

## 2) 상태 정의
- `READY`: 생성 완료, 실행 대기
- `RUNNING`: 오케스트레이션 실행 중
- `FAILED_RETRYABLE`: 재시도 가능한 실패 발생
- `NEEDS_HUMAN_APPROVAL`: 사람 승인/반려 필요
- `DONE`: 정상 완료

## 3) 전이 규칙
| 현재 상태 | 이벤트 | 다음 상태 | 규칙 |
|---|---|---|---|
| (없음) | `TASK_CREATED` | `READY` | `/task/create` 성공 시 |
| `READY` | `RUN_REQUESTED` | `RUNNING` | `/task/run` 성공 시 |
| `RUNNING` | `EXECUTION_SUCCEEDED` | `DONE` | reporter 단계까지 정상 종료 |
| `RUNNING` | `EXECUTION_FAILED_RETRYABLE` | `FAILED_RETRYABLE` | 재시도 가능한 오류 |
| `FAILED_RETRYABLE` | `RETRY_STARTED` | `RUNNING` | 재시도 1회 시작 |
| `FAILED_RETRYABLE` | `RETRY_EXHAUSTED` | `NEEDS_HUMAN_APPROVAL` | 재시도 소진 |
| `RUNNING` | `POLICY_BLOCKED` | `NEEDS_HUMAN_APPROVAL` | 위험 액션/정책 위반 탐지 |
| `NEEDS_HUMAN_APPROVAL` | `HUMAN_APPROVED` | `RUNNING` | 승인 후 실행 재개 |
| `NEEDS_HUMAN_APPROVAL` | `HUMAN_REJECTED` | `DONE` | 반려 종료(실패 사유 기록) |

## 4) 금지 전이
- `DONE -> RUNNING` 금지
- `READY -> DONE` 직접 전이 금지
- `NEEDS_HUMAN_APPROVAL -> DONE` 직접 종료는 `HUMAN_REJECTED` 이벤트만 허용

## 5) 재시도 정책
- 기본 재시도 횟수: 1회
- 재시도 대상: `FAILED_RETRYABLE`만 허용
- 재시도 실패 시 반드시 `NEEDS_HUMAN_APPROVAL`로 전이

## 6) 승인 정책
- 아래 이벤트는 자동 진행 금지:
  - 외부 전송 요청
  - 금지 명령 포함 요청
  - 비허용 경로 접근 요청
- 승인 결과는 이벤트 로그로 기록:
  - `HUMAN_APPROVED`
  - `HUMAN_REJECTED`

## 7) 상태 조회 응답 규칙
- `RUNNING`: `current_stage`, `last_event_at` 포함
- `FAILED_RETRYABLE`: `retry_count`, `last_error` 포함
- `NEEDS_HUMAN_APPROVAL`: `approval_reason`, `next_action` 포함
- `DONE`: `result` 또는 `final_reason` 포함

## 8) 다이어그램 (텍스트)
```text
(create)
  -> READY
  -> RUNNING
     -> DONE
     -> FAILED_RETRYABLE -> RUNNING (retry once)
     -> FAILED_RETRYABLE -> NEEDS_HUMAN_APPROVAL (retry exhausted)
     -> NEEDS_HUMAN_APPROVAL -> RUNNING (approved)
     -> NEEDS_HUMAN_APPROVAL -> DONE (rejected)
```
