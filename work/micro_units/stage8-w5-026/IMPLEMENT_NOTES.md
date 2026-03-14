# Implement Notes

## Changed Files
- `app/main.py`
- `tests/test_incident_runtime_smoke.py`
- `tests/test_stage8_contract.py`

## Rollback Plan
- incident path에서 `planning_provenance`와 `INCIDENT_PLAN_GENERATED`를 제거하고, 기존 deterministic action card 경로만 유지한다.
- `planned_actions`와 `action_cards` 이중 유지가 충돌하면 incident path를 다시 `action_cards -> action_results` 최소 경로로 복귀시킨다.
- runtime smoke 회귀가 planner provenance에 한정되면 incident 공통 계약 반영분만 되돌리고 task planner/campaign 변경은 유지한다.

## Known Risks
- incident planner는 아직 deterministic이라 AI-first incident planning 자체는 여전히 후속 단계다.
- event 순서가 바뀌면서 기존 incident smoke와 approval-flow 테스트가 미세하게 깨질 수 있다.
- provider selection과 planning provenance를 함께 기록하면서 로그량이 조금 늘어난다.
