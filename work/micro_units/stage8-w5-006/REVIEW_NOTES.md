# Review Notes

## Security / Policy Review
- provider selection은 audit/observability 용으로 남기되, approval policy 자체를 우회하면 안 된다.
- `external_send` 같은 위험 플래그는 provider 선택과 별개로 그대로 human approval 흐름을 유지해야 한다.
- task status에 노출되는 provider 정보는 민감한 secret 없이 id/type/engine/model 수준으로 제한한다.

## Architecture / Workflow Review
- 이번 단위의 목적은 `config -> runtime selection -> event/status exposure` 연결이다.
- 실제 provider 호출이 아니라 selection logging부터 넣는 것이 현재 단계에 맞다.
- YAML parser는 현재 registry 스키마에 맞는 최소 범위로 유지하고, 추후 필요 시 교체 가능해야 한다.
- CLI/MCP/API가 모두 같은 status payload를 공유하도록 service layer 쪽에서 노출하는 것이 맞다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `python3 -m unittest tests.test_model_registry_contract tests.test_model_registry_runtime`
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-006 8`
- QA worktree에서는 runtime smoke로 task/incident provider selection event를 실제로 확인한다.

## Review Verdict
- 조건부 승인 (Approved as Routing Visibility Increment)
- 조건:
  1. selection 결과는 event/status에만 노출하고 실제 LLM 호출까지 확장하지 말 것
  2. approval policy와 별개 경로를 만들지 말 것
  3. parser는 현재 `model_registry.yaml` 스키마를 안정적으로 처리할 것
