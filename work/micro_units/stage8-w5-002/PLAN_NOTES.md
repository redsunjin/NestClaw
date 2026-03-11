# Plan Notes

## Scope
- `task`와 `incident` 생성/실행 흐름을 감싸는 단일 에이전트 진입 API(`agent submit/status/events`)를 추가한다.
- 규칙 기반 라우터를 추가해 단일 요청을 `meeting_summary` 또는 `incident_orchestration`으로 분기한다.
- CLI를 기존 task 전용 메뉴에서 단일 agent 요청 흐름으로 정리한다.
- 계약/런타임 테스트와 기본 문서를 갱신해 새 진입점을 고정한다.

## Out of Scope
- 실제 LLM 기반 intent classification
- GUI 운영 콘솔 구현
- 다중 템플릿/다중 도메인 자동 라우팅
- live RAG provider 구현

## Acceptance Criteria
- `POST /api/v1/agent/submit` 한 곳으로 일반 task와 incident 요청을 생성/실행할 수 있다.
- `GET /api/v1/agent/status/{task_id}`와 `GET /api/v1/agent/events/{task_id}`가 workflow를 숨기고 일관된 조회 경로를 제공한다.
- CLI가 `agent submit -> status -> result` 흐름을 기본 진입점으로 사용한다.
- runtime smoke가 agent task/incident 라우팅을 검증한다.
- `bash scripts/run_micro_cycle.sh run stage8-w5-002 8`가 통과한다.

## Risks
- 규칙 기반 라우터가 의도와 다르게 task/incident를 오분류할 수 있다.
- 기존 task/incident 전용 엔드포인트와 상태 모델이 달라지면 회귀가 생길 수 있다.
- CLI를 너무 단순화하면 기존 회의요약 입력 힌트가 줄어들 수 있다.

## Test Plan
- 정적/단위:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
- 런타임:
  - `python3 -m unittest tests.test_runtime_smoke tests.test_incident_runtime_smoke tests.test_agent_entrypoint_smoke`
- 품질게이트:
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-002 8`
