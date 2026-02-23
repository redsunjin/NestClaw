# 정책 화이트리스트 초안 (v0.1)

## 1) 목적
로컬 업무 위임 오케스트레이터가 접근 가능한 경로/도구를 명시적으로 제한한다.

## 2) 기본 정책
- 기본값: `DENY`
- 명시 허용된 경로/도구만 실행 가능
- 미등록 요청은 `BLOCKED_POLICY`로 기록 후 `NEEDS_HUMAN_APPROVAL` 전환

## 3) 허용 경로 (초안)
| 구분 | 경로 | 권한 | 비고 |
|---|---|---|---|
| 입력 | `workspace/inputs/**` | read | 사용자 제공 업무 입력 |
| 템플릿 | `workspace/templates/**` | read | 템플릿 정의 파일 |
| 작업 산출물 | `workspace/reports/**` | read/write | 보고서/결과물 저장 |
| 로그 | `workspace/logs/**` | append | 감사 로그 전용 |

주의:
- 개인 영역(예: 개인 사진, 개인 메신저 데이터)은 허용하지 않는다.
- 루트 또는 시스템 전역 경로 접근은 금지한다.

## 4) 허용 도구 (초안)
| 도구 | 허용 액션 | 제한 |
|---|---|---|
| File Tool | read/write(허용 경로 내) | 경로 화이트리스트 강제 |
| Task DB | read/write | Task 관련 테이블만 접근 |
| Template Renderer | render | 템플릿 ID 검증 필수 |

## 5) 금지 명령/행위
- `rm`, `mv` 등 파괴적 파일 조작(정책 승인 전)
- 외부 네트워크 전송(메일/웹훅/API 호출)
- 개인 데이터 폴더 탐색
- 승인 없는 대량 수정

## 6) 정책 위반 처리
1. 요청 차단 (`BLOCKED_POLICY`)
2. 위반 사유 로그 기록
3. 필요 시 `NEEDS_HUMAN_APPROVAL` 큐 등록
4. 승인 전 자동 재실행 금지

## 7) 이벤트 로그 필드 (최소)
```json
{
  "event_type": "BLOCKED_POLICY",
  "task_id": "task_xxx",
  "actor": "policy_engine",
  "reason_code": "PATH_NOT_ALLOWED",
  "detail": "requested path is not in whitelist",
  "created_at": "2026-02-22T08:00:00Z"
}
```
