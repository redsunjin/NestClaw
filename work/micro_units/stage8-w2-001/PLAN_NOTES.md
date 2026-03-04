# Plan Notes

## Scope
- `app/incident_rag.py` 스켈레톤 파일 추가
  - `fetch_knowledge_evidence(query, team, time_range)`
  - `fetch_system_signals(incident_id, service, window)`
  - 공통 타임아웃/예외 포맷 기본틀 포함
- `app/incident_mcp.py` 스켈레톤 파일 추가
  - `execute_redmine_action(method, payload, actor_context)`
  - Dry-run 모드 기본 처리 분기 포함
- 기존 런타임 동작을 깨지 않도록 현재 `app/main.py`는 인터페이스 import 가능 수준까지만 연결

## Out of Scope
- 실제 외부 RAG API 네트워크 호출 구현
- 실제 Redmine MCP 인증/토큰 연동
- Incident 런타임 경로의 end-to-end 실행 로직 완성
- 운영 Sandbox 티켓 생명주기 검증

## Acceptance Criteria
- `app/incident_rag.py`, `app/incident_mcp.py` 파일이 생성되고 인터페이스 시그니처가 상세설계 문서와 일치한다.
- 스켈레톤은 import 시 즉시 예외를 발생시키지 않는다.
- 민감정보 로그 노출 없이 실패/미구현 상태를 명시적으로 반환하거나 예외화한다.
- Stage 8 계약 테스트(`tests/test_stage8_contract.py`)가 계속 통과한다.
- Dev-QA cycle stage 8 실행 시 기존 PASS/SKIP 규칙을 유지한다.

## Risks
- 인터페이스 시그니처 불일치로 후속 통합 비용 증가 위험
- 예외 포맷 불일치로 승인/재시도 경로 연동 시 회귀 위험
- 스켈레톤 단계에서 임시 하드코딩이 남아 정책 위반을 유발할 위험

## Test Plan
- 정적 계약 테스트: `python3 -m unittest tests.test_stage8_contract`
- 전체 게이트 확인: `bash scripts/run_dev_qa_cycle.sh 8`
- 구현 완료 후 추가 예정:
  - `tests/test_incident_adapter_contract.py`로 함수 시그니처/기본 반환/오류 포맷 검증
