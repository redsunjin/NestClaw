# Implement Notes

## Changed Files
- `app/agent_planner.py`
- `app/main.py`
- `app/services/orchestration_service.py`
- `configs/model_registry.yaml`
- `scripts/run_dev_qa_cycle.sh`
- `tests/test_agent_planner_contract.py`
- `tests/test_agent_planner_runtime.py`
- `tests/test_model_registry_contract.py`
- `tests/test_stage8_contract.py`

## Rollback Plan
- planner baseline에 회귀가 생기면 `app/agent_planner.py`와 `task_type=plan_actions` routing rule을 되돌리고, `task` workflow를 기존 deterministic summary-only planner로 복귀시킨다.
- status/event 계약 문제 시 `planning_provenance` 노출과 `TASK_PLAN_*` 이벤트 추가분을 롤백하고 기존 provider selection / provider invocation 경로만 유지한다.
- QA cycle 실패가 planner runtime에만 한정되면 `NEWCLAW_ENABLE_LLM_PLANNER=0` degraded mode로 운영 연속성을 유지한 채 원인 수정 후 재적용한다.

## Known Risks
- planner 출력은 JSON-only 계약에 의존하므로 provider 응답이 흔들리면 `llm_error_fallback` 비율이 높아질 수 있다.
- 현재 task planner의 허용 도구는 `internal.summary.generate`, `slack.message.send` 두 개뿐이라 broader multi-step planning 기대치와 차이가 있다.
- summary action을 첫 번째 action으로 강제해 기존 report 루프와 호환시키므로, 후속 planner 확장 시 이 가정이 깨지지 않게 주의해야 한다.
