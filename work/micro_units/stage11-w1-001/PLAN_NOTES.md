# Plan Notes

## Scope
- Stage 8 readiness에서 계속 blocker로 남는 external env를 한 문서와 한 검증 절차로 묶는다.
- sandbox/live env 항목별 의미, owner, 예시 형식, required/optional 여부를 canonical handoff profile로 정리한다.
- 운영자가 repo 전체를 뒤지지 않고 handoff checklist만으로 누락 여부를 판단할 수 있게 만든다.
- 가능하면 local validation 절차 또는 lightweight validator script를 제공하고, 관련 contract를 보강한다.

## Out of Scope
- 실제 sandbox/live env 발급
- Redmine/Slack 외부 시스템 onboarding 자체 수행
- Stage 8 live rehearsal 성공까지 보장
- planner/runtime core semantics 변경
- production secret manager 연동

## AI-First Planner Design
- 이번 단계는 planner를 더 똑똑하게 만드는 작업이 아니라, 운영자와 상위 agent가 external env blocker를 같은 방식으로 해석하게 만드는 control-plane 작업이다.
- 현재 blocker는 코드 실패가 아니라 external env handoff friction이므로, scattered docs보다 canonical profile이 우선이다.
- upper-agent 입장에서도 `무엇이 비어 있어서 BLOCKED인지`를 한 payload/문서 세트에서 읽을 수 있어야 하므로, readiness와 운영 문서가 같은 vocabulary를 공유해야 한다.
- 구현은 새 env profile 문서, 예시 템플릿, validator/contract 보강을 중심으로 진행하는 편이 적절하다.

## Acceptance Criteria
- external env handoff profile 문서가 존재하고, Stage 8 required env의 의미/owner/example/validation 기준이 표 또는 구조화된 형태로 정리된다.
- 운영자가 바로 쓸 수 있는 env template 또는 equivalent handoff artifact가 존재한다.
- readiness rerun 전 체크 절차가 runbook과 분리되지 않고 profile 문서와 연결된다.
- `tests.test_stage11_contract`와 필요 시 관련 contract/runtime smoke가 통과한다.
- `bash scripts/run_dev_qa_cycle.sh 11`이 통과한다.

## Risks
- env profile이 현재 readiness bundle 요구사항과 어긋나면 오히려 잘못된 handoff를 만든다.
- example 값을 너무 구체적으로 쓰면 실제 secret처럼 오해될 수 있으므로 placeholder 수준을 지켜야 한다.
- validator를 과도하게 엄격하게 만들면 local dev와 ops handoff가 불필요하게 깨질 수 있다.
- readiness 문서와 profile 문서가 다시 분리된 vocabulary를 쓰면 BLOCKED 해석이 흐려질 수 있다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage11-w1-001`
- `bash scripts/run_micro_cycle.sh gate-review stage11-w1-001`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_stage11_contract`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 11`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_micro_cycle.sh run stage11-w1-001 11`
