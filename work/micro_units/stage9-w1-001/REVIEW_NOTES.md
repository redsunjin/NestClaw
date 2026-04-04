# Review Notes

## Security / Policy Review
- planner/executor 공통화는 실행 권한을 넓히는 작업이 아니므로 기존 approval gate, actor context, tool allowlist 경계를 그대로 유지해야 한다.
- 공통 executor helper는 payload binding과 dispatch만 담당하고, `incident`의 live/dry-run 결정이나 approval 판단을 우회하면 안 된다.
- 공통 action result contract를 만들더라도 request payload에는 기존 redaction 규칙이 유지되어야 하며, 민감정보를 raw event/status에 새로 노출하면 안 된다.

## Architecture / Workflow Review
- `app/main.py`에 흩어진 action materialization, binding, execution dispatch를 공통 helper 또는 service 계층으로 옮기되, task planner 결정과 incident planner 결정 자체는 분리된 채로 유지하는 편이 맞다.
- 공통 schema는 최소 공통 필드만 강제하고, incident의 `evidence_links`, `mcp_call` 같은 workflow 전용 필드는 그대로 보존해야 한다.
- event/status contract는 유지하고 내부 구현만 정리해야 하므로, UI나 API payload shape를 먼저 흔드는 방식의 리팩터는 이번 단계에 맞지 않는다.

## QA Gate Review
- `tests.test_stage9_contract`로 stage9 campaign/scaffold와 stage9 cycle 진입점을 고정해야 한다.
- task/incident runtime smoke에서 공통 executor 경로 회귀를 잡아야 하며, 특히 event ordering과 `action_results` shape가 유지되는지 확인해야 한다.
- `bash scripts/run_dev_qa_cycle.sh 9`가 stage9 baseline gate로 통과해야 하고, 이후 implement/evaluate 단계에서도 같은 명령을 재사용할 수 있어야 한다.

## Review Verdict
- 진행 승인.
- 이번 단계는 공통 planner/executor rail 정리에 집중하고, incident AI planner 확장과 UI 변경은 다음 MWU로 미룬다.
