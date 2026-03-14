# Review Notes

## Security / Policy Review
- binding은 allowlisted token만 지원해야 하고 임의 표현식 평가를 허용하면 안 된다.
- resolved payload를 결과에 남길 때는 slack text처럼 민감할 수 있는 값은 adapter의 masking 규칙을 그대로 따라야 한다.
- cross-action binding이 추가돼도 policy gate는 executor 이전에 그대로 유지돼야 한다.

## Architecture / Workflow Review
- planner와 executor 책임을 분리해 `planner=순서`, `executor=binding+dispatch`로 두는 방향이 맞다.
- task path에서 먼저 binding을 넣고 incident path는 context signature만 맞추는 단계적 적용이 적절하다.
- binding token helper는 `_dispatch_planned_action` 주변 공통 함수로 두는 편이 좋다.

## QA Gate Review
- task planner runtime smoke가 ticket/slack payload binding 결과를 검증해야 한다.
- incident runtime smoke는 공통 executor 변경 이후에도 기존 경로가 유지되는지 확인해야 한다.
- QA canonical cycle에서 full stage 8 runtime smoke를 다시 통과시켜야 한다.

## Review Verdict
- 진행 승인.
- 이번 단계는 token 기반의 제한된 binding에 한정하고, richer structured binding은 후속 단계로 미룬다.
