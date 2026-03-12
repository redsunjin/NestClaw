# Review Notes

## Security / Policy Review
- classifier 결과가 task/incident 분기를 결정하더라도 기존 auth/approval/policy gate를 우회하면 안 된다.
- live classifier 호출은 env-gated 이어야 하고, secret은 event/status에 기록하면 안 된다.
- fallback은 deterministic heuristic으로 유지해 운영 중 예측 가능성을 확보해야 한다.

## Architecture / Workflow Review
- 이번 단위의 목적은 `auto routing` 판단을 LLM adapter 뒤로 보내는 것이다.
- provider invocation 전체가 아니라 classifier 한 점만 live 시도하고, 실패 시 fallback 하는 구조가 현재 단계에 맞다.
- status/event에 classification provenance를 남겨 이후 quality tuning이 가능해야 한다.
- service layer에서 classifier callback을 주입받는 방식이 CLI/MCP/API 공통화에 맞다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `python3 -m unittest tests.test_intent_classifier_contract tests.test_intent_classifier_runtime tests.test_agent_entrypoint_smoke`
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-007 8`
- QA worktree에서는 patched live call과 fallback runtime 둘 다 확인한다.

## Review Verdict
- 조건부 승인 (Approved as Safe Auto-Routing Upgrade)
- 조건:
  1. live classifier failure는 항상 heuristic fallback으로 흡수할 것
  2. classification provenance를 status/event에 남길 것
  3. direct `task_kind=task|incident` 경로는 기존 동작을 유지할 것
