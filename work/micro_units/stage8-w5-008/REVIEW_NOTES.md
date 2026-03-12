# Review Notes

## Security / Policy Review
- LM Studio endpoint는 local-only default(`http://127.0.0.1:1234`)로 취급하고 secret/token은 status/event에 남기지 않는다.
- classifier가 실패해도 기존 heuristic fallback을 유지해 auto-routing 안정성을 해치지 않아야 한다.
- local OpenAI-compatible endpoint 호출이 추가되어도 approval/policy/auth 흐름은 그대로 유지되어야 한다.

## Architecture / Workflow Review
- 이번 단위는 provider registration + classifier adapter 확장에 한정한다.
- `app/intent_classifier.py`에서 engine별 adapter 분기만 추가하고, broader provider invocation 단계와 분리한다.
- LM Studio는 OpenAI-compatible local adapter로 취급하고, model autodiscovery는 classifier 내부 helper에서 해결한다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract tests.test_model_registry_contract tests.test_intent_classifier_contract`
  - `python3 -m unittest tests.test_intent_classifier_runtime tests.test_agent_entrypoint_smoke tests.test_model_registry_runtime`
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-008 8`
- LM Studio live call은 network dependency 없이 patched response 중심으로 테스트한다.

## Review Verdict
- 조건부 승인 (Approved as Local Provider Adapter Extension)
- 조건:
  1. LM Studio 미가동 시 반드시 heuristic fallback으로 흡수할 것
  2. model auto-detection 실패가 hard failure가 아니라 fallback reason으로 남을 것
  3. `classify_intent` provider selection이 문서/테스트와 함께 고정될 것
