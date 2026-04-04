# Implement Notes

## Changed Files
- [x] `IDEATION_ONEPAGER.md`
  - 제품 프레이밍을 `조직용 orchestration runtime/control plane`으로 정리하고 degraded mode 설명을 planning baseline 기준으로 정리했다.
- [x] `API_CONTRACT.md`
  - v0.1 목표 제품 정의를 control plane posture에 맞게 정리했다.
- [x] `app/services/planner_executor_service.py`
  - 공통 provider-selection recording helper, report write helper, result finalization helper를 추가했다.
- [x] `app/services/__init__.py`
  - planner/executor 후반부 helper export를 추가했다.
- [x] `app/main.py`
  - task/incident workflow가 shared provider-selection recording helper를 사용하도록 정리했다.
  - task/incident workflow가 shared report write / finalize helper를 사용하도록 정리했다.
- [x] `scripts/run_dev_qa_cycle.sh`
  - stage9 QA cycle에 task/incident runtime smoke를 optional regression으로 연결했다.
- [x] `tests/test_planner_executor_service.py`
  - provider-selection recording, report write, finalization helper unit test를 추가했다.
- [x] `tests/test_stage8_contract.py`
  - posture 및 provider-selection helper 이동에 맞춰 static contract 기대값을 갱신했다.
- [x] `tests/test_stage9_contract.py`
  - stage9 campaign의 두 번째 G1 MWU와 shared helper 범위를 contract에 고정했다.

## Rollback Plan
- helper rollback 대상:
  - `app/services/planner_executor_service.py`
  - `app/services/__init__.py`
  - `app/main.py`
- contract/runtime regression rollback 대상:
  - `scripts/run_dev_qa_cycle.sh`
  - `tests/test_planner_executor_service.py`
  - `tests/test_stage8_contract.py`
  - `tests/test_stage9_contract.py`
  - `IDEATION_ONEPAGER.md`
  - `API_CONTRACT.md`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_stage8_contract tests.test_stage9_contract tests.test_planner_executor_service`
  - `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_planner_executor_service tests.test_stage9_contract tests.test_agent_planner_runtime tests.test_incident_runtime_smoke`
  - `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`

## Known Risks
- `MODEL_PROVIDER_SELECTED` emission이 shared helper로 이동했기 때문에, 이후 static contract는 `main wiring + service event emission` 조합을 기준으로 유지해야 한다.
- finalization helper는 `result`와 `completed_at`를 status 변경 전에 넣는 순서를 전제로 하므로, 이후 `_set_status` semantics를 바꾸면 helper contract도 함께 갱신해야 한다.
- stage9 QA cycle에 runtime smoke를 묶었지만, browser/playwright와 live env readiness는 여전히 env-gated skip에 의존한다.
