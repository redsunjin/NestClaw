# Review Notes

## Security / Policy Review
- provider invocation은 승인/정책 이전에 외부 전송을 우회하면 안 된다. summary workflow에서는 기존 policy block 이후에만 호출되어야 한다.
- provider selection이 `requires_human_approval`를 남기더라도, 이번 단위는 report generation path에 한정하고 approval semantics는 기존 정책을 유지한다.
- API key/base URL은 env 기반으로만 받고, 기본값이 외부 전송을 강제하지 않도록 안전한 fallback이 필요하다.

## Architecture / Workflow Review
- selection과 invocation을 분리한다. selection은 `model_registry`, invocation은 별도 service/module로 둔다.
- 첫 consumer는 `meeting_summary` 하나로 제한하고, incident 쪽은 후속 planner 단계로 남긴다.
- runtime provenance는 `task["provider_invocation"]`, 이벤트 로그, 결과 메타데이터 중 최소 두 곳 이상에 남겨 추적 가능해야 한다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_provider_invoker_contract tests.test_provider_invoker_runtime tests.test_stage8_contract`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-011 8`
- live 호출은 mock/patch 기반 runtime smoke로 검증하고, 실제 네트워크 의존 테스트는 넣지 않는다.

## Review Verdict
- 승인 (Approved with Safe Fallback Constraint)
- 조건:
  1. live provider 실패 시 task 실행이 실패로 끝나지 말고 기존 템플릿 summary로 fallback 할 것
  2. invocation provenance 이벤트를 남길 것
  3. 이번 단위에서 incident workflow까지 무리하게 확장하지 말 것
