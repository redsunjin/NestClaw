# Plan Notes

## Scope
- NestClaw의 제품 정의를 `정책·승인·감사 하에 다양한 도구를 계획적으로 사용하는 orchestration AI agent`로 재정렬한다.
- 문서 우선순위를 `operator surface 우선`에서 `AI-first planning/execution maturity 우선`으로 수정한다.
- 전문가 운영 프로토콜에서 A03 LLM Orchestrator의 책임을 명시해, planner 설계 검토가 절차에서 빠지지 않게 한다.
- `rfs-cli -> NestClaw -> external tools` 계층을 상위 아키텍처 문서에 반영한다.
- 관련 계약 테스트를 갱신해 이후 문서가 다시 fallback-first / UI-first로 돌아가지 않게 고정한다.

## Out of Scope
- 실제 LLM multi-step planner 구현
- provider invocation 확대
- tool execution/runtime 로직 변경
- Web Console 기능 추가

## AI-First Planner Design
- 기본 사용자/상위 호출자는 고수준 목표만 넘기고, 계획/도구 선택의 주체는 NestClaw가 맡는다.
- 현재 runtime의 heuristic/template 경로는 유지하되, 문서와 acceptance 기준에서는 `degraded mode`로만 정의한다.
- 다음 MWU의 구현 목표는 `LLM planner -> policy gate -> multi-step executor`를 기본 경로로 올리는 것이다.
- `rfs-cli -> NestClaw -> external tools` 계층에서도 승인/감사/정책 집행 권한은 NestClaw에 남긴다.

## Acceptance Criteria
- [NEXT_WORK_GROUPS_2026-03-13.md](/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation/NEXT_WORK_GROUPS_2026-03-13.md)에서 G2가 G1보다 먼저 오고, 현재 추천 포커스가 G2로 바뀐다.
- [EXPERT_AGENT_OPERATING_PROTOCOL_2026-03-13.md](/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation/EXPERT_AGENT_OPERATING_PROTOCOL_2026-03-13.md)에 A03의 planner design 책임이 반영된다.
- 상위 제품 정의 문서에 `AI-first orchestration agent`, `degraded mode`, `rfs-cli -> NestClaw -> external tools` 개념이 반영된다.
- [tests/test_stage8_contract.py](/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation/tests/test_stage8_contract.py)에서 새 방향을 검사한다.

## Risks
- 문구를 너무 급하게 바꾸면 현재 구현 상태보다 과장된 제품 정의로 보일 수 있다.
- A03를 절차에 반영하는 수준이 애매하면, 문서만 늘고 실제 운영 규칙은 그대로 남을 수 있다.
- 기존 Stage 8 문서군의 `incident first vertical` 정의와 충돌하지 않도록 범위 표현을 조심해야 한다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage8-w5-023`
- `bash scripts/run_micro_cycle.sh gate-review stage8-w5-023`
- `python3 -m unittest tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-023 8`
