# Review Notes

## Security / Policy Review
- canonical taxonomy는 backend policy를 대체하면 안 되고, 기존 approval/policy decision을 더 명확히 노출하는 수준에 머물러야 한다.
- `env_blocked`, `policy_blocked`, `approval_pending`을 같은 값처럼 섞어 쓰면 operator가 대응 책임을 잘못 해석할 수 있으므로 분리된 reason code가 필요하다.
- requester에게도 state summary는 보여줄 수 있지만, approver/admin 전용 detail 권한은 그대로 유지돼야 한다.

## Architecture / Workflow Review
- shared taxonomy helper를 만들고 capability manifest, orchestration status, recent, bundle이 같은 함수를 써야 surface parity가 유지된다.
- 기존 `status` 필드는 그대로 두고, 추가 필드는 `state_summary` 또는 readiness summary의 canonical fields로 붙이는 편이 역호환에 유리하다.
- quickstart/console은 새 taxonomy를 길게 설명하기보다 signal/chip/summary 수준으로만 노출해야 한다.

## QA Gate Review
- HTTP, CLI, MCP가 모두 canonical reason field를 포함하는지 runtime smoke로 확인해야 한다.
- approval-needed task와 normal done task를 함께 써서 `policy_blocked`와 `completed`를 구분 검증해야 한다.
- stage10 cycle 전체가 다시 PASS여야 하고, env-gated skip 외 새 failure가 없어야 한다.

## Review Verdict
- 진행 승인.
- 이번 단계는 taxonomy normalization에 집중하고, transport/auth hardening은 다음 item으로 넘긴다.
