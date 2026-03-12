# Plan Notes

## Scope
- `configs/model_registry.yaml`에 LM Studio local provider를 등록한다.
- intent classifier가 `http://localhost:1234` 기반 OpenAI-compatible local endpoint를 호출할 수 있게 확장한다.
- LM Studio model이 config에 없거나 `auto`일 때 `/v1/models`에서 자동 감지할 수 있게 한다.
- 관련 contract/runtime test와 사용 문서를 추가한다.

## Out of Scope
- task/incident 본 실행 경로의 실제 provider invocation 연결
- OpenAI cloud provider 호출 추가
- operator UI
- live RAG adapter 고도화
- sandbox/live rehearsal

## Acceptance Criteria
- model registry에 LM Studio provider가 등록되고 `classify_intent`는 해당 provider를 선택한다.
- `NEWCLAW_ENABLE_LLM_INTENT=1`일 때 classifier가 LM Studio OpenAI-compatible endpoint를 호출할 수 있다.
- LM Studio model이 `auto`일 때 첫 번째 loaded model을 자동 선택한다.
- 호출 실패 시 기존 heuristic fallback이 유지된다.
- 관련 unit/runtime tests와 `bash scripts/run_micro_cycle.sh run stage8-w5-008 8`가 통과한다.

## Risks
- LM Studio OpenAI-compatible 응답 형식이 예상과 다르면 parsing 보강이 필요할 수 있다.
- loaded model 자동감지가 실패하면 fallback으로만 동작할 수 있다.
- endpoint base URL normalization을 잘못 처리하면 `/v1` 중복/누락 문제가 생길 수 있다.

## Test Plan
- 정적:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract tests.test_model_registry_contract tests.test_intent_classifier_contract`
- 런타임:
  - `python3 -m unittest tests.test_intent_classifier_runtime tests.test_agent_entrypoint_smoke tests.test_model_registry_runtime`
- 품질 게이트:
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-008 8`
