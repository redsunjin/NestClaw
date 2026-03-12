# Plan Notes

## Scope
- `configs/model_registry.yaml`를 읽는 경량 runtime loader를 추가한다.
- task/incident 실행 시 provider selection을 계산하고 task state 및 event log에 남긴다.
- status payload에 provider selection을 노출해 CLI/MCP/API에서 동일하게 보이게 한다.
- model registry contract/unit test와 runtime smoke를 추가한다.

## Out of Scope
- 실제 외부 LLM provider 호출
- intent classifier 구현
- model registry 편집 UI
- YAML 외 일반 설정 포맷 지원
- live sandbox rehearsal

## Acceptance Criteria
- `configs/model_registry.yaml`가 runtime에서 로드된다.
- task 또는 incident 실행 시 `MODEL_PROVIDER_SELECTED` 이벤트가 남는다.
- status payload에 `provider_selection`이 포함된다.
- unit/runtime tests와 `bash scripts/run_micro_cycle.sh run stage8-w5-006 8`가 통과한다.

## Risks
- YAML 의존성 없이 파서를 직접 넣을 경우 스키마 변경 내성이 낮을 수 있다.
- provider selection heuristic이 기존 approval/policy와 충돌하면 혼선을 줄 수 있다.
- event/status 노출이 task/incident 경로별로 달라지면 표면 계약이 어긋난다.

## Test Plan
- 정적:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
- 런타임:
  - `python3 -m unittest tests.test_model_registry_contract tests.test_model_registry_runtime`
- 품질 게이트:
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-006 8`
