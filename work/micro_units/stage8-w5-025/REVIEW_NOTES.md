# Review Notes

## Security / Policy Review
- planner가 ticket tool을 고르더라도 실행 가능 도구는 runtime eligibility helper가 제한해야 한다.
- task path의 ticket create는 project id가 없으면 후보군에 들어가면 안 된다.
- policy gate와 approval 전환은 planner 확장 후에도 executor 이전에 그대로 유지해야 한다.
- provenance에는 선택된 action뿐 아니라 eligible tool 목록도 남겨서 감사 가능해야 한다.

## Architecture / Workflow Review
- 이번 단계는 task path에서만 planner 후보군을 넓히고, incident 공통화는 다음 MWU로 미룬다.
- report 루프가 첫 action의 `output_text`를 summary 결과로 사용하므로 summary first invariant는 유지해야 한다.
- redmine ticket payload는 우선 task input/metadata 기반으로 만들고, richer cross-action data binding은 후속 단계로 남긴다.

## QA Gate Review
- contract test는 eligibility 기준, ordering, planner provenance를 고정해야 한다.
- runtime smoke는 `redmine.issue.create`가 task path에서 실제 planned_action / action_result로 남는지 확인해야 한다.
- QA canonical cycle로 planner runtime smoke와 grouped stage 8 흐름을 다시 통과시켜야 한다.

## Review Verdict
- 진행 승인.
- 이번 단위는 task path candidate expansion에 한정하고, incident planner 공통화는 별도 MWU로 다룬다.
