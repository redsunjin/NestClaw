# Plan Notes

## Scope
- 제품 전체 목적을 `정책·승인·감사 하에 다양한 도구를 사용하는 실행형 에이전트`로 문서에 고정한다.
- Stage 8 incident 문서군을 `제품 전체 목표`가 아니라 `첫 번째 high-risk vertical/use case`로 재정렬한다.
- README / onepager / next plan / tasks / API contract / Stage 8 문서의 충돌 문구를 정리한다.
- 정렬 상태를 고정하는 정적 계약 테스트를 추가한다.

## Out of Scope
- 코드 runtime 동작 변경
- tool registry / tool planner 실제 구현
- provider invocation 확장
- operator UI 구현
- sandbox/live rehearsal

## Acceptance Criteria
- 상위 문서에서 제품 목적이 `도구를 정책적으로 사용하는 실행형 에이전트`로 일관되게 표현된다.
- Incident 관련 문서는 Stage 8이 `첫 번째 vertical/use case`임을 명시한다.
- API contract는 현재 구현 범위가 `task/incident` workflow family임을 명확히 말한다.
- 정적 계약 테스트와 `bash scripts/run_micro_cycle.sh run stage8-w5-009 8`가 통과한다.

## Risks
- 기존 Stage 8 기록을 지나치게 바꾸면 역사적 맥락이 흐려질 수 있다.
- 문서마다 목적/범위/현재상태 레벨이 달라 과도한 통일은 오히려 정확성을 해칠 수 있다.
- incident vertical과 broader execution agent를 섞어 쓰면 다시 모호해질 수 있다.

## Test Plan
- 정적:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
- 품질 게이트:
  - `bash scripts/run_micro_cycle.sh run stage8-w5-009 8`
