# Implement Notes

## Changed Files
- [x] `app/intent_classifier.py`
  - env-gated live classifier + heuristic fallback + provider provenance 추가
- [x] `app/main.py`
  - classifier singleton / callback wiring을 orchestration runtime에 연결
- [x] `app/services/orchestration_service.py`
  - `task_kind=auto`를 classifier callback으로 분리하고 `intent_classification` 상태/이벤트 기록 추가
- [x] `configs/model_registry.yaml`
  - `task_type: classify_intent`를 local provider로 고정하는 routing rule 추가
- [x] `tests/test_intent_classifier_contract.py`
  - fallback / llm success / malformed response / unsupported provider unit test 추가
- [x] `tests/test_intent_classifier_runtime.py`
  - agent facade runtime에서 classifier provenance와 route override 검증 추가
- [x] `tests/test_model_registry_contract.py`
  - `classify_intent` routing rule 계약 추가
- [x] `tests/test_stage8_contract.py`
  - classifier wiring / file presence / gate wiring 계약 추가
- [x] `scripts/run_dev_qa_cycle.sh`
  - classifier contract/runtime smoke를 stage8 gate에 연결
- [x] `work/micro_units/stage8-w5-007/*`
  - plan/review/implement/evaluate 자산 생성

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `app/intent_classifier.py`
  - `app/main.py`
  - `app/services/orchestration_service.py`
  - `configs/model_registry.yaml`
  - `tests/test_intent_classifier_contract.py`
  - `tests/test_intent_classifier_runtime.py`
  - `tests/test_model_registry_contract.py`
  - `tests/test_stage8_contract.py`
  - `scripts/run_dev_qa_cycle.sh`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract tests.test_model_registry_contract tests.test_intent_classifier_contract`
  - `env PATH=\"/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH\" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-intent-feature.db bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- live classifier adapter가 없는 환경에서는 fallback 중심으로만 검증될 수 있다.
- provider selection과 classifier selection이 분리되면 later provider invocation 단계에서 조정이 필요할 수 있다.
- feature worktree에서는 runtime dependency 부재로 일부 smoke가 `SKIP`될 수 있다.
