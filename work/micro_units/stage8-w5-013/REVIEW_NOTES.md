# Review Notes

## Security / Policy Review
- Slack은 외부 도구이므로 production registry 자동 반영이 아니라 reviewable draft 생성까지만 허용한다.
- Slack live mode는 env flag와 bot token이 모두 있어야 하며, dry-run을 기본으로 유지한다.
- incident planner가 Slack action을 추가해도 기존 policy/approval gate를 그대로 통과해야 한다.

## Architecture / Workflow Review
- Slack tool은 existing `execution_call` contract 위에서 추가하는 것이 맞다.
- assistant-driven registration은 runtime tool creation이 아니라 `draft -> review -> merge` 흐름으로 두는 것이 현재 정책 모델과 맞다.
- API/CLI/MCP가 같은 ToolDraftService를 공유하도록 구현해 표면별 분기 로직을 최소화한다.

## QA Gate Review
- catalog surface에 Slack capability가 나타나는지 확인한다.
- incident runtime이 Slack planned action을 생성하는지 확인한다.
- CLI/MCP/API에서 tool draft 생성 및 조회가 되는지 확인한다.
- Slack adapter dry-run/live contract를 별도 테스트로 검증한다.

## Review Verdict
- 승인 (Approved with draft-only registration guardrail)
