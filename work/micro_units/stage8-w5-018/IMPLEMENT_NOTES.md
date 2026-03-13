# Implement Notes

## Changed Files
- `tests/runtime_test_utils.py`
- `tests/test_runtime_reset_resilience.py`

## Rollback Plan
- helper 변경이 부작용을 만들면 `tests/runtime_test_utils.py`를 기존 table delete 방식으로 되돌리고 resilience test를 제거하면 된다.
- production code는 건드리지 않았으므로 rollback 범위는 test helper와 test file로 제한된다.

## Known Risks
- `/tmp` 경로 기준 fresh recreate는 test isolation에는 유리하지만, 테스트가 특정 DB 파일 지속성을 기대하면 맞지 않는다.
- helper가 `app.cli` orchestration service까지 동기화하므로 다른 test module이 추가되면 sync 대상이 더 필요할 수 있다.
