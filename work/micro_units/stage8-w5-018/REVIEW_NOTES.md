# Review Notes

## Security / Policy Review
- 테스트 헬퍼 변경만 있으므로 production 권한 모델에는 영향이 없어야 한다.
- temp SQLite 파일 삭제는 `/tmp` 경로로 제한해 실제 로컬 데이터 삭제를 피한다.
- malformed recovery는 테스트 안정화 목적이어야 하며 일반 runtime 오류를 숨기면 안 된다.

## Architecture / Workflow Review
- reset 단계에서 새 store를 만들면 `STATE_STORE` 뿐 아니라 orchestration service deps도 같이 갱신해야 한다.
- helper는 temp sqlite에 대해서만 fresh recreation을 수행하고, 그 외 backend는 기존 clear flow를 유지하는 것이 맞다.
- 회귀 테스트는 fake module 수준에서 helper의 store swap을 검증하면 충분하다.

## QA Gate Review
- helper resilience unit test 추가
- `tests.test_runtime_smoke` 반복 실행으로 실제 문제 재현 케이스를 검증
- micro evaluate와 canonical QA cycle까지 다시 통과해야 한다.

## Review Verdict
- Proceed. 문제는 기능 회귀가 아니라 test isolation이므로 helper 수준 보강으로 먼저 닫는 것이 맞다.
