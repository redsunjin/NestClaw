# Review Notes

## Security / Policy Review
- recent payload에는 planner provenance의 요약만 노출하고 raw provider invocation이나 민감 payload는 포함하지 않는다.
- UI에 표시되는 planned tool list는 이미 authorized task status 범위 안의 정보만 사용해야 한다.
- degraded mode/fallback reason을 표시하더라도 auth model은 그대로 유지하고, requester가 자기 task만 보도록 기존 권한 검사를 유지한다.

## Architecture / Workflow Review
- provenance surface는 backend 최소 확장 + frontend renderer 확장으로 끝내는 편이 맞다. planner logic 자체를 건드릴 필요는 없다.
- quickstart와 console이 같은 summary helper를 각자 가지더라도 표시 규칙은 동일해야 한다.
- recent endpoint는 `planning_source`, `planning_provider_id`, `planned_tool_ids` 같은 요약 필드를 제공하는 정도로 제한하는 편이 적절하다.

## QA Gate Review
- agent recent/runtime smoke가 새 provenance summary 필드를 검증해야 한다.
- web console runtime test는 quickstart/console asset에 planner provenance UI 요소와 renderer가 포함됐는지 확인해야 한다.
- canonical QA cycle에서 fastapi runtime smoke까지 다시 통과시켜 regressions를 막아야 한다.

## Review Verdict
- 진행 승인.
- 이번 단계는 operator visibility 개선에 한정하고, auto-refresh/polling과 deeper plan drill-down은 후속 작업으로 남긴다.
