# Plan Notes

## Scope
- MCP stdio server의 startup, transport, actor/auth 경계를 upper-agent 관점에서 다시 문서화한다.
- `README`, `NESTCLAW_AGENT_INTEGRATION_SPEC.md`, `NESTCLAW_INTEGRATION_EXAMPLES.md`에 MCP 연결 순서와 운영 전제를 더 구체적으로 반영한다.
- 반복 호출자가 바로 검증할 수 있도록 MCP smoke 또는 contract 검증을 필요한 수준으로 보강한다.
- production-ready remote transport를 구현하는 대신, 현재 stdio baseline과 future deployment boundary를 명확히 분리한다.

## Out of Scope
- 새로운 remote MCP transport 서버 구현
- OAuth/JWT auth scheme 자체 변경
- dashboard chat panel 추가
- tool/approval/runtime core semantics 변경
- Stage 8 sandbox/live env 발급

## AI-First Planner Design
- 이번 단계는 planner intelligence가 아니라 상위 agent가 NestClaw MCP를 안정적으로 붙이는 배포/운영 계약을 정리하는 단계다.
- 상위 agent 입장에서는 `어떻게 서버를 띄우는가`, `어떤 actor 권한으로 붙는가`, `어떤 tool이 안전한가`, `stdio와 운영 배포 경계가 어디인가`가 중요하다.
- 따라서 문서와 smoke는 기능 breadth보다 `startup repeatability`, `auth expectation`, `safe control boundary`를 우선해야 한다.
- 기존 `agent.submit/status/events/recent/report/bundle`과 `catalog.manifest`를 canonical loop로 유지하고, MCP는 그 loop를 안정적으로 전달하는 transport라는 점을 분명히 해야 한다.

## Acceptance Criteria
- MCP startup/stdio baseline, actor/auth boundary, safe/elevated control 분리가 문서에 명시된다.
- upper-agent가 repo 문서만 읽고 stdio MCP를 붙일 수 있는 concrete example이 보강된다.
- `tests.test_mcp_server_smoke`, `tests.test_stage10_contract`, 필요 시 관련 contract/runtime smoke가 통과한다.
- Stage 10 QA cycle이 다시 PASS이고 env-gated skip 외 신규 failure가 없다.

## Risks
- 문서가 현재 runtime보다 과장되면 upper-agent 통합자가 존재하지 않는 transport/auth 기능을 기대할 수 있다.
- stdio baseline과 future deployment guidance를 섞으면 운영자가 현재 지원 범위를 오해할 수 있다.
- safe control과 elevated control의 예시가 흐리면 상위 agent가 approval/apply/live를 과하게 호출할 위험이 있다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage10-w1-004`
- `bash scripts/run_micro_cycle.sh gate-review stage10-w1-004`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_mcp_server_smoke tests.test_stage10_contract`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 10`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_micro_cycle.sh run stage10-w1-004 10`
