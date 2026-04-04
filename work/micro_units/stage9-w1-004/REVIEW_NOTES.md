# Review Notes

## Security / Policy Review
- planner rationale와 fallback detail은 operator 해석을 위한 정보여야 하며, 승인 정책을 우회하는 직접 action control이 되면 안 된다.
- quickstart는 여전히 requester 중심 surface여야 하므로 elevated-only governance 정보와 혼동되지 않게 유지해야 한다.
- incident payload에 이미 들어간 rationale를 UI가 그대로 읽되, operator surface에서 민감한 raw context를 새로 노출하지는 않아야 한다.

## Architecture / Workflow Review
- status payload의 canonical contract는 유지하고, web console/quickstart JS가 그것을 더 풍부하게 시각화하는 구조가 적절하다.
- UI vocabulary는 task/incident 공통으로 `planner summary -> action rail -> execution drill-down` 3층으로 정리하는 것이 맞다.
- recent/history 카드에도 planner source, degraded/fallback, planned/executed flow를 축약해서 보여주는 것이 operator 스캔 속도에 유리하다.

## QA Gate Review
- web console runtime test는 새 투명성 surface가 HTML/JS에 실제 연결돼 있는지 확인해야 한다.
- full regression은 stage9 contract, web console runtime, incident runtime smoke, capability manifest runtime을 함께 본다.
- 최종 gate는 `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`다.

## Review Verdict
- 진행 승인.
- 이번 단위는 G3의 첫 구현 단위로 타당하며, chat panel이나 deeper console IA 변경은 후속으로 미룬다.
