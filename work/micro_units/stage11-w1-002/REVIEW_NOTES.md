# Review Notes

## Security / Policy Review
- operator handoff packet은 승인 결정을 대신하는 surface가 아니라, 기존 approval/report/bundle evidence를 compact하게 전달하는 read/export layer여야 한다.
- requester/reviewer가 packet을 조회하더라도 approval action history나 elevated detail을 자동으로 더 많이 보게 만들면 안 되므로, 기존 approval access level을 그대로 따라가야 한다.
- markdown export는 사람에게 전달하기 쉬워야 하지만 secret, raw token, 과도한 approval action detail을 포함하지 않는 편이 맞다.

## Architecture / Workflow Review
- packet은 `agent.bundle`의 경쟁자가 아니라 compact operator view model이어야 하며, canonical source는 기존 status/events/report/approval/bundle 위에 있어야 한다.
- blocked / approval-pending / completed 분류는 runtime taxonomy와 approval availability를 재사용해 계산하고, 다른 naming을 새로 만들지 않는 편이 적절하다.
- HTTP/CLI/MCP에 같은 packet contract를 열되, CLI plain output은 markdown rendering, JSON/MCP는 structured payload를 중심으로 두는 구성이 자연스럽다.

## QA Gate Review
- HTTP runtime smoke, CLI smoke, MCP smoke가 새 handoff surface를 모두 확인해야 한다.
- stage11 contract는 handoff spec 문서, route/tool/command surface, current MWU state를 함께 고정해야 한다.
- `bash scripts/run_dev_qa_cycle.sh 11` 전체 PASS와 env-gated skip 외 신규 failure 없음이 기준이다.

## Review Verdict
- 진행 승인.
- 이번 단계는 canonical handoff packet spec, HTTP/CLI/MCP export surface, markdown rendering, contract/smoke 보강 범위로 제한한다.
