# Review Notes

## Security / Policy Review
- A04 관점: AI-first로 가더라도 approval, RBAC, audit는 deterministic gate로 유지해야 한다.
- 제품 정의를 `AI가 기본 실행기`로 올리더라도, heuristic/template 경로는 `degraded mode`로만 남겨야 한다.
- `rfs-cli -> NestClaw -> external tools` 구조에서도 직접 실행 권한의 소유자는 NestClaw이며, 상위 호출자에게 승인 우회 권한을 주면 안 된다.

## Architecture / Workflow Review
- A01 관점: 현재 계획 문서는 제품 목표보다 operator surface 개선을 먼저 두고 있어 우선순위가 뒤집혀 있다.
- A03 관점: planner/tool selection이 아직 주 경로가 아니므로, 다음 주력 그룹은 `G2 Planning and Execution Maturity`여야 한다.
- 운영 프로토콜에는 A03의 planner design review가 명시돼야 한다. 다만 이번 MWU에서는 별도 gate 추가보다 프로토콜 문구와 책임 선언을 먼저 정렬한다.
- incident는 broader execution agent의 첫 번째 vertical로 유지하되, 제품 전체 정의는 orchestration AI agent로 올려야 한다.

## QA Gate Review
- 정적 계약 테스트로 제품 정의/우선순위/프로토콜 문구를 고정한다.
- 이번 MWU는 문서/프로토콜 변경이므로 canonical QA는 `tests.test_stage8_contract`와 stage 8 cycle 재실행으로 충분하다.
- 런타임 동작 자체는 바꾸지 않으므로 live rehearsal 범위는 포함하지 않는다.

## Review Verdict
- 진행 승인.
- 구현 범위는 문서/프로토콜/백로그/계약 테스트 정렬로 제한한다.
- 후속 MWU는 실제 `LLM planner` 구현으로 이어져야 한다.
