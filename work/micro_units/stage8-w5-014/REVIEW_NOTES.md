# Review Notes

## Security / Policy Review
- apply action은 draft-only guardrail을 유지하면서 approver/admin만 허용해야 한다.
- runtime refresh가 있어도 source registry는 immutable로 남기고, overlay만 변경해야 한다.
- 테스트 격리를 위해 overlay와 draft artifacts를 reset helper에서 정리해야 한다.

## Architecture / Workflow Review
- tool registry loader가 base + overlay merge를 지원하는 것이 가장 단순하다.
- ToolDraftService가 apply를 직접 수행하되, 실제 registry 반영과 refresh는 callback으로 분리하는 것이 현재 구조에 맞다.
- CLI/MCP는 별도 service instance를 들고 있으므로 apply 후 catalog refresh를 각 표면에서 보정해야 한다.

## QA Gate Review
- API apply 후 `/api/v1/tools`에서 새 tool이 보여야 한다.
- CLI `tool-apply` 후 `tools` 목록에 새 tool이 보여야 한다.
- MCP `catalog.apply_draft` 후 `catalog.list`가 즉시 새 tool을 반환해야 한다.
- overlay writer/unit contract가 별도로 검증되어야 한다.

## Review Verdict
- 승인 (Approved with overlay-only apply path)
