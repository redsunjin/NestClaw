# Plan Notes

## Scope
- Stage 11에서 이미 정리된 operator handoff packet, external env handoff profile, pilot evidence matrix, blocked-to-resumed runbook을 하나의 반복 가능한 pilot acceptance cycle로 묶는다.
- 최소한 pilot 판단 시 필요한 입력 문서, acceptance checklist 순서, blocked / fail / operational hold 분류 기준을 한 문서 또는 동등한 artifact로 고정한다.
- 가능하면 lightweight validator 또는 contract 보강을 통해 acceptance packet이 빠진 문서 없이 닫히는지 자동 점검한다.
- go / no-go / hold 판단이 임의 메모가 아니라 같은 evidence vocabulary로 읽히도록 guide와 테스트를 연결한다.

## Out of Scope
- Stage 8 외부 env 자체 발급
- live sandbox rehearsal 자체 자동화 확장
- planner logic, provider selection, dashboard UX 변경
- 새로운 remote operator gateway 또는 human chat surface 추가
- 조직별 승인 정책 세부 튜닝

## AI-First Planner Design
- 이번 단계는 새 agent intelligence를 추가하는 작업이 아니라, 상위 agent와 operator가 pilot acceptance를 같은 evidence grammar로 해석하게 만드는 operational closure 단계다.
- acceptance cycle은 새로운 실행 표면이 아니라 기존 `handoff`, `bundle`, readiness bundle, evidence matrix 위에 얹히는 최종 판단 절차여야 한다.
- 따라서 핵심은 “어떤 증적이 있어야 go/no-go/hold를 결정할 수 있는가”를 기계와 사람이 모두 읽을 수 있게 고정하는 것이다.
- blocked, fail, operational hold를 혼동하지 않도록 canonical taxonomy와 operator handoff packet vocabulary를 그대로 재사용하는 편이 적절하다.

## Acceptance Criteria
- canonical pilot acceptance cycle 문서 또는 동등한 artifact가 존재한다.
- acceptance 판단에 필요한 입력이 `handoff packet`, `env handoff profile`, `pilot evidence matrix`, `blocked-to-resumed runbook`, `latest readiness/QA evidence`로 명시된다.
- `blocked`, `fail`, `operational hold`의 판단 기준이 문서와 contract에서 일치한다.
- 관련 contract/test와 `bash scripts/run_dev_qa_cycle.sh 11`이 통과한다.
- operator 또는 upper-agent가 acceptance cycle 문서만 보고 pilot 판단 절차를 재현할 수 있다.

## Risks
- acceptance cycle이 기존 runbook/evidence matrix 내용을 단순 재복사만 하면 운영 판단 기준이 여전히 분산된 상태로 남을 수 있다.
- blocked와 operational hold를 제대로 구분하지 못하면 Stage 8처럼 env 의존 issue가 제품 failure로 오해될 수 있다.
- validator를 과하게 엄격하게 만들면 실제 운영 메모 갱신만으로도 false negative가 날 수 있으므로 canonical required inputs만 검사하는 선이 적절하다.
- pilot judgment 문구가 추상적이면 upper-agent가 인간 승인 필요 상황을 자동 실패로 과도하게 해석할 위험이 있다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage11-w1-004`
- `bash scripts/run_micro_cycle.sh gate-review stage11-w1-004`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_stage11_contract`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 11`
- 필요 시 acceptance validator smoke를 추가하고 Stage 11 cycle에 연결한다.
