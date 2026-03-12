# Plan Notes

## Scope
- 현재 `task`와 `incident`가 따로 가진 planner/executor 경로를 비교해 공통화 대상과 분리 유지 대상을 정리한다.
- 다음 구현 단위의 목표를 `planned_actions -> policy gate -> execution adapter dispatch -> report` 공통 루프로 고정한다.
- `meeting_summary`도 `internal tool action`으로 표현해 tool planning 대상에 포함시키는 설계를 기준안으로 채택한다.
- 필요한 데이터 계약, adapter registry 구조, 단계별 마이그레이션 순서를 문서로 정의한다.

## Out of Scope
- 이번 단위에서 실제 코드 리팩터링/구현
- incident live provider invocation 확장
- live RAG adapter 구현
- operator UI

## Acceptance Criteria
- 공통 루프의 목표 계약이 문서로 고정된다.
- `task`/`incident` 각각 무엇을 planner가 만들고 executor가 소비하는지 명확히 설명된다.
- `internal summary generation`을 tool capability로 포함할지 여부와 이유가 결정된다.
- 마이그레이션 단계를 `무중단 리팩터링` 관점으로 제시한다.

## Risks
- 공통화 범위를 너무 넓게 잡으면 다음 구현 단위가 과도하게 커질 수 있다.
- summary generation을 tool로 모델링하지 않으면 planner 공통화가 다시 무너질 수 있다.
- 반대로 internal action까지 tool registry에 넣을 때 registry 의미가 흐려질 수 있다.

## Test Plan
- 계획/리뷰 게이트:
  - `bash scripts/run_micro_cycle.sh gate-plan stage8-w5-012`
  - `bash scripts/run_micro_cycle.sh gate-review stage8-w5-012`
- 정적 검증:
  - `python3 -m unittest tests.test_stage8_contract`
