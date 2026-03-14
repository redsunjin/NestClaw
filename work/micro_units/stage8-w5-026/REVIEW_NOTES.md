# Review Notes

## Security / Policy Review
- planner provenance는 incident action approval logic를 약화시키면 안 된다.
- incident path에서 planner가 고른 action이 무엇이든 기존 policy gate와 approval queue가 executor 이전에 그대로 적용돼야 한다.
- eligible tool 목록은 감사/운영 관측 용도로만 쓰고, 허용되지 않은 tool을 실행 가능하게 만들면 안 된다.

## Architecture / Workflow Review
- incident planning helper를 task planner와 같은 관측 계약으로 맞추는 방향은 적절하다.
- 이번 단계에서는 deterministic planner 유지가 맞고, event/status/API 계약을 먼저 맞춘 뒤 후속 MWU에서 AI planner로 올리는 편이 안정적이다.
- `action_cards`와 `planned_actions`를 동시에 유지해 하위 호환을 지키는 것이 안전하다.

## QA Gate Review
- contract test로 incident planning provenance와 campaign workflow assets를 고정한다.
- runtime smoke는 `DONE` 경로와 `NEEDS_HUMAN_APPROVAL` 경로 둘 다 provenance를 확인해야 한다.
- QA canonical cycle로 incident runtime smoke와 grouped self-eval을 다시 통과시켜야 한다.

## Review Verdict
- 진행 승인.
- incident path를 AI planner로 올리기 전에 planner/provenance 계약부터 공통화하는 접근이 맞다.
