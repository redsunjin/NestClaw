# 회의요약 템플릿 연결 테스트 계획 (v0.1)

## 1) 목적
`meeting_summary` 템플릿이 `create/run/status` 흐름에서 정상 동작하는지 검증한다.

## 2) 전제조건
- `API_CONTRACT.md` 기준 엔드포인트가 구현되어 있어야 한다.
- `NON_IT_WORK_TEMPLATES.md`의 템플릿 1 입력 필드가 반영되어 있어야 한다.

## 3) 테스트 시나리오
## 시나리오 A: 정상 처리
1. `/task/create`로 회의요약 작업 생성
2. `/task/run` 실행
3. `/task/status/{task_id}` 폴링
4. 최종 `DONE` + report_path 확인

기대 결과:
- 상태 전이: `READY -> RUNNING -> DONE`
- 출력에 핵심 논점/액션아이템/확인필요 섹션 포함

## 시나리오 B: 필수값 누락
1. `meeting_date` 없이 `/task/create` 요청

기대 결과:
- `400 INVALID_REQUEST`
- 오류 메시지에 누락 필드 명시

## 시나리오 C: 정책 차단
1. 입력에 외부 전송 요청 포함
2. 실행 시도

기대 결과:
- `NEEDS_HUMAN_APPROVAL` 전환
- `BLOCKED_POLICY` 이벤트 로그 기록

## 4) 검증 체크포인트
- [ ] 상태 조회가 Task ID 기준으로 일관됨
- [ ] 실패/차단 사유가 사용자 메시지로 노출됨
- [ ] 보고서 형식이 템플릿 정의와 일치함
- [ ] 승인 필요 시 자동 진행되지 않음

## 5) 실행 메모
- 현재는 테스트 계획 문서 단계이며, 실제 실행은 API 구현 후 진행한다.
