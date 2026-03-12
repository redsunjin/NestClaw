# Plan Notes

## Scope
- model registry selection 결과를 실제 provider 호출로 연결하는 공통 invocation layer를 추가한다.
- 첫 concrete consumer는 `meeting_summary` task 실행 경로로 제한한다.
- provider invocation provenance를 status/event/result에 남기고, live 호출 실패 시 기존 템플릿 렌더러로 안전하게 fallback 한다.
- contract/runtime 테스트와 운영 문서를 현재 상태에 맞게 갱신한다.

## Out of Scope
- incident planner/action-card의 LLM화
- multi-step tool planning
- live RAG adapter 확장
- 새로운 외부 provider 종류 추가
- operator UI

## Acceptance Criteria
- `model registry selection -> provider invocation` 코드 경로가 실제 존재하고, summary workflow에서 사용된다.
- 지원 provider(`lmstudio`, `ollama`, `openai-compatible api`)에 대한 invocation adapter가 공통 서비스로 정리된다.
- task 상태 또는 결과에서 invocation provenance를 확인할 수 있고, `MODEL_PROVIDER_INVOKED` 이벤트가 남는다.
- live 호출 실패 또는 비활성 시 기존 summary renderer로 정상 fallback 한다.
- `bash scripts/run_micro_cycle.sh run stage8-w5-011 8`와 QA worktree canonical cycle이 통과한다.

## Risks
- live provider 응답 형식이 자유로워 report contract가 깨질 수 있다.
- network/API key 의존이 생기므로 테스트가 flaky해질 수 있다.
- invocation layer를 너무 일반화하면 이번 단위가 과도하게 커질 수 있다.

## Test Plan
- 정적/계약:
  - `python3 -m unittest tests.test_provider_invoker_contract tests.test_stage8_contract`
- 런타임:
  - `python3 -m unittest tests.test_provider_invoker_runtime tests.test_model_registry_runtime tests.test_tool_cli_smoke`
- 품질 게이트:
  - `bash scripts/run_micro_cycle.sh run stage8-w5-011 8`
