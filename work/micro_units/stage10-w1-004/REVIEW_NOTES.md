# Review Notes

## Security / Policy Review
- MCP guidance는 현재 권한 모델을 단순화해서 설명하면 안 되고, requester/reviewer vs approver/admin 경계를 분명히 유지해야 한다.
- 문서 예제가 `approve`, `apply_draft`, `rollback`, `live` 같은 elevated control을 기본 흐름처럼 보이게 만들면 안 된다.
- stdio startup 예제는 허용되지만, remote transport/auth를 이미 지원하는 것처럼 과장하면 운영 리스크가 커진다.

## Architecture / Workflow Review
- MCP는 별도 엔진이 아니라 HTTP/CLI와 같은 orchestration runtime의 transport 표면이라는 점을 문서에서 분명히 해야 한다.
- startup, actor headers/identity, safe control, bundle/report observe loop를 같은 integration narrative 안에서 읽히게 정리하는 편이 좋다.
- deployment guidance는 `현재 지원하는 stdio baseline`과 `향후 hardening boundary`를 구분해 써야 한다.

## QA Gate Review
- 문서 변경 후에도 `tests.test_mcp_server_smoke`와 `tests.test_stage10_contract`는 유지돼야 한다.
- 가능하면 README / integration spec / examples 사이에 MCP 진입 순서가 서로 어긋나지 않는지 contract 성격으로 확인해야 한다.
- stage10 cycle 전체가 다시 PASS이고 env-gated skip 외 신규 failure가 없어야 한다.

## Review Verdict
- 진행 승인.
- 이번 단계는 문서와 smoke hardening에 집중하고, 실제 remote transport 구현은 범위 밖으로 유지한다.
