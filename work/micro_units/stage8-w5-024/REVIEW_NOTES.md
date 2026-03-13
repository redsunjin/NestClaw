# Review Notes

## Security / Policy Review
- planner가 slack action을 고르더라도 정책 차단과 승인 큐는 기존 gate가 그대로 맡아야 한다.
- task planner는 실행 가능한 도구를 registry allowlist로 제한해야 하며, 임의 tool id를 그대로 실행하면 안 된다.
- fallback reason과 planner provenance는 이벤트/상태에 남겨 나중에 감사 가능해야 한다.

## Architecture / Workflow Review
- 이번 구현은 planner만 교체하고 executor/report 루프는 유지하는 것이 맞다.
- task workflow에서 summary를 첫 action으로 강제하면 기존 report generation 코드와 호환된다.
- multi-step planning의 첫 단계로 task path에 summary/slack만 허용하는 좁은 범위가 적절하다.
- incident는 별도 vertical이므로 후속 MWU에서 planner 공통화로 확장한다.

## QA Gate Review
- contract test로 planner 모듈, model registry rule, run_dev_qa_cycle stage8 연결을 고정한다.
- runtime test는 `LLM planner live success`와 `fallback` 두 경로를 모두 확인해야 한다.
- QA canonical cycle에서 grouped self-eval까지 다시 통과해야 한다.

## Review Verdict
- 진행 승인.
- task path에 한정한 AI-first planner 승격으로 범위를 고정한다.
- plan validation과 provenance 없이는 merge하지 않는다.
