# Implement Notes

## Changed Files
- [x] `configs/model_registry.yaml`
  - `local_lmstudio` provider 등록 및 `classify_intent` routing rule을 LM Studio로 전환
- [x] `app/intent_classifier.py`
  - LM Studio OpenAI-compatible chat adapter 추가
  - `/v1/models` 기반 auto model discovery 추가
  - `NEWCLAW_LMSTUDIO_BASE_URL`, `NEWCLAW_LMSTUDIO_API_KEY` env 지원 추가
- [x] `tests/test_model_registry_contract.py`
  - LM Studio provider/routing 계약 반영
- [x] `tests/test_intent_classifier_contract.py`
  - LM Studio llm call / auto model detection / fallback 검증 추가
- [x] `tests/test_intent_classifier_runtime.py`
  - runtime provenance가 `local_lmstudio`로 기록되는지 검증 업데이트
- [x] `tests/test_stage8_contract.py`
  - LM Studio env/helper/config wiring 계약 추가
- [x] `README.md`
  - LM Studio env 예시와 timeout/model autodiscovery 사용법 반영
- [x] `TASKS.md`
  - LM Studio local provider support 완료 반영
- [x] `NEXT_STAGE_PLAN_2026-02-24.md`
  - current diagnosis에 LM Studio local adapter 반영
- [x] `work/micro_units/stage8-w5-008/*`
  - plan/review/implement/evaluate 자산 생성

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `configs/model_registry.yaml`
  - `app/intent_classifier.py`
  - `tests/test_model_registry_contract.py`
  - `tests/test_intent_classifier_contract.py`
  - `tests/test_intent_classifier_runtime.py`
  - `tests/test_stage8_contract.py`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_stage8_contract tests.test_model_registry_contract tests.test_intent_classifier_contract`
  - `env PATH=\"/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH\" NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-lmstudio-feature.db bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- LM Studio loaded model이 느리면 classifier는 timeout 뒤 heuristic fallback으로 동작한다.
- `model: auto`는 `/v1/models` 첫 번째 항목을 사용하므로, 여러 모델이 떠 있을 때 의도한 모델과 다를 수 있다.
- 현재는 intent classifier에만 LM Studio를 연결했고, broader provider invocation 단계는 아직 아니다.
