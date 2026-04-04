# Review Notes

## Security / Policy Review
- incident AI planner는 action 선택만 확장해야 하며, approval policy를 우회하거나 risk level을 낮추는 경로를 만들면 안 된다.
- deterministic fallback은 live provider 실패 시 안전 경로여야 하므로, planner 실패가 곧 실행 실패로 직결되지 않게 유지해야 한다.
- planner rationale을 payload/report에 넣더라도 민감 원문 전체를 외부 시스템에 과도하게 전파하지 않도록 기존 summary 수준을 넘지 않아야 한다.

## Architecture / Workflow Review
- `AgentPlanner`에 incident 전용 prompt/normalization/fallback을 추가하고, `app/main.py`는 decision을 action payload로 바꾸는 wiring만 남기는 구조가 적절하다.
- workflow-level `provider_selection`과 planner-level `planning_provenance.provider_selection`은 목적이 다르므로 둘 다 유지하는 것이 맞다.
- incident report와 outbound payload는 planner rationale을 읽을 수 있게 하되, canonical execution contract는 계속 `planned_actions + planning_provenance + action_results + result`다.

## QA Gate Review
- contract test는 model registry routing, incident planner source/fallback semantics, stage9 campaign 문서 상태를 함께 검증해야 한다.
- runtime smoke는 `llm success`, `deterministic fallback`, `approval path`, `2-action incident`를 포함해야 한다.
- 최종 gate는 `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`다.

## Review Verdict
- 진행 승인.
- 이번 단위는 G2 시작점으로 타당하며, incident live retrieval 확장과 UI 반영은 후속 단계로 둔다.
