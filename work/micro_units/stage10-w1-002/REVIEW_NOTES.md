# Review Notes

## Security / Policy Review
- UI gating은 기존 role policy를 대체하면 안 되고, 단지 더 명확하게 드러내야 한다.
- requester/reviewer에게 approval detail/history나 apply-like control을 직접 노출하면 오작동과 policy confusion을 유발할 수 있으므로 기본 숨김이 맞다.
- 다만 UI에서 숨긴다고 backend 권한이 완화되면 안 되므로, JS handler도 non-elevated role에서 친화적 차단 메시지를 주는 수준으로 유지해야 한다.

## Architecture / Workflow Review
- role-aware UI는 기존 `/api/v1/agent/*`, `approval.*`, `catalog.*` contract를 그대로 재사용해야 한다.
- quickstart는 requester용 lightweight surface, console은 operator surface라는 분리를 더 분명히 하되, 별도 chat/TUI 방향으로 확장하지 않는다.
- gating은 `data-role-scope + runtime guard + role summary copy` 세 층으로 구현하는 편이 단순하고 유지보수에 유리하다.

## QA Gate Review
- HTML/JS/CSS 정적 서빙 테스트에서 role-scoped markup이 존재하는지 확인해야 한다.
- runtime smoke에서 requester role 기준 approval/detail 접근 흐름이 읽기용 summary로 남는지, approver/admin에서 detail/action이 계속 가능한지 확인해야 한다.
- stage10 cycle 전체가 다시 PASS여야 하고, env-gated skip 외에 새 failure가 없어야 한다.

## Review Verdict
- 진행 승인.
- 이번 단계는 surface hardening에 집중하고, taxonomy normalization과 MCP deployment hardening은 다음 item으로 미룬다.
