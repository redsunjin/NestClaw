# Review Notes

## Security / Policy Review
- execution bundle은 export 편의 기능이지 권한 확대 기능이 아니어야 한다.
- approval detail/history는 기존 approval role policy를 그대로 따라야 하며, requester bundle에는 queue summary만 남겨야 한다.
- bundle에 포함되는 report preview, events, capabilities는 기존 read access를 재사용해야 하고, secret/env/token 값은 절대 포함되면 안 된다.

## Architecture / Workflow Review
- 새 bundle은 기존 contract 위에 얹는 aggregator여야 하고, 별도 planner/executor 경로를 만들면 안 된다.
- orchestration service가 canonical bundle shape를 만들고, HTTP/CLI/MCP는 그 결과를 thin adapter로 노출하는 구조가 맞다.
- capability manifest 전체를 매번 깊게 중첩하기보다 upper-agent handoff에 필요한 summary와 canonical source를 함께 주는 쪽이 payload 안정성에 유리하다.

## QA Gate Review
- HTTP/CLI/MCP surface parity가 핵심이므로 세 표면을 모두 runtime smoke로 검증해야 한다.
- approval pending task와 completed task를 각각 만들어 approval summary/detail과 report availability shape를 확인해야 한다.
- stage10 campaign/scaffold 존재 여부를 잡는 contract test를 추가해 다음 MWU가 같은 경로를 재사용하게 한다.

## Review Verdict
- 진행 승인.
- 이번 MWU는 `control plane export` 정리에 집중하고, dashboard role gating과 taxonomy normalization은 다음 item으로 넘긴다.
