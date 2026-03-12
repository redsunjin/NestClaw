# Review Notes

## Security / Policy Review
- tool CLI도 HTTP와 동일하게 actor identity/role을 명시적으로 받아야 한다.
- approval approve/reject는 `acted_by == actor_id` 규칙과 approver/admin role 검증을 그대로 따라야 한다.
- CLI 출력이 JSON일 때도 approval queue/task 식별자를 누락 없이 남겨 후속 감사가 가능해야 한다.

## Architecture / Workflow Review
- 이번 단위의 목적은 `사람/스크립트/AI`가 공통으로 쓸 수 있는 안정적 CLI 표면을 만드는 것이다.
- menu CLI는 유지하되, 기본 고도화는 non-interactive subcommand 쪽에 둔다.
- agent submit/status/events는 `OrchestrationService`를 직접 호출하고, approval approve/reject는 같은 application 코어를 직접 호출하는 방향이 맞다.
- CLI는 로컬 HTTP 호출을 제거해야 이후 MCP tool adapter와 구조를 공유하기 쉽다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `python3 -m unittest tests.test_agent_entrypoint_smoke tests.test_incident_runtime_smoke tests.test_tool_cli_smoke`
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-004 8`
- QA worktree에서는 `.venv`에서 CLI smoke를 실제로 재실행해 runtime state와 충돌이 없는지 본다.

## Review Verdict
- 조건부 승인 (Approved as Tool Surface Increment)
- 조건:
  1. 기존 메뉴형 CLI는 깨지지 않게 유지할 것
  2. tool CLI는 pure JSON 출력과 명확한 exit code를 지원할 것
  3. approval 경로 권한 검증을 우회하지 말 것
