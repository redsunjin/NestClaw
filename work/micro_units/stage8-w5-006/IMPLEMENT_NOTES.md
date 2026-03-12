# Implement Notes

## Changed Files
- [x] `app/model_registry.py`
  - `configs/model_registry.yaml`용 경량 loader/cache와 provider selection helper 추가
- [x] `app/main.py`
  - task/incident execution 시 provider selection context 계산 및 `MODEL_PROVIDER_SELECTED` event 기록 추가
- [x] `app/services/orchestration_service.py`
  - status payload에 `provider_selection` 노출 추가
- [x] `tests/test_model_registry_contract.py`
  - registry parse/rule selection unit test 추가
- [x] `tests/test_model_registry_runtime.py`
  - task/incident runtime에서 provider selection event/status 검증 추가
- [x] `tests/test_stage8_contract.py`
  - model registry runtime wiring 계약 추가
- [x] `scripts/run_dev_qa_cycle.sh`
  - stage8 model registry contract/runtime smoke를 QA cycle에 연결
- [x] `README.md`
  - runtime provider selection logging 반영
- [x] `TASKS.md`
  - model registry runtime loader 항목 완료 반영
- [x] `NEXT_STAGE_PLAN_2026-02-24.md`
  - 다음 우선순위를 intent classifier / 실제 provider invocation 중심으로 조정
- [x] `work/micro_units/stage8-w5-006/*`
  - MWU plan/review/implement/evaluate 자산 추가

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `app/model_registry.py`
  - `app/main.py`
  - `app/services/orchestration_service.py`
  - `tests/test_model_registry_contract.py`
  - `tests/test_model_registry_runtime.py`
  - `tests/test_stage8_contract.py`
  - `scripts/run_dev_qa_cycle.sh`
  - `README.md`
  - `TASKS.md`
  - `NEXT_STAGE_PLAN_2026-02-24.md`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- 경량 YAML parser는 registry 형식이 크게 바뀌면 보강이 필요하다.
- selection heuristic이 과도하면 later intent classifier 도입 때 충돌할 수 있다.
- feature worktree에서는 runtime dependency 부재로 일부 smoke가 `SKIP`될 수 있다.
