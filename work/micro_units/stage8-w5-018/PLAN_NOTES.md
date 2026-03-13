# Plan Notes

## Scope
- `tests/runtime_test_utils.py`가 temp SQLite state store를 더 강하게 초기화하도록 보강한다.
- malformed SQLite 파일이 있어도 reset이 새 store를 재생성하게 만든다.
- helper 회귀 방지용 테스트를 추가한다.

## Out of Scope
- production persistence 로직 자체 변경
- PostgreSQL test isolation 변경
- Web Console 기능 추가

## Acceptance Criteria
- `tests.test_runtime_smoke` 단독 실행이 malformed temp DB 때문에 깨지지 않는다.
- runtime reset helper가 temp SQLite store를 재생성할 수 있다.
- 회귀 방지용 테스트가 추가된다.

## Risks
- 테스트 헬퍼가 state store를 갈아끼우면 CLI/runtime service가 old store를 참조할 수 있으므로 동기화가 필요하다.
- temp DB 기준으로 너무 공격적으로 지우면 다른 개발 흐름에 영향을 줄 수 있으므로 `/tmp` 경로로 제한한다.
- SQLite error 메시지 분기가 너무 좁거나 넓으면 다른 실제 오류를 숨길 수 있다.

## Test Plan
- `python3 -m unittest tests.test_runtime_reset_resilience tests.test_runtime_smoke`
- 같은 명령을 연속 2회 실행해 반복성 확인
- `bash scripts/run_micro_cycle.sh run stage8-w5-018 8`
