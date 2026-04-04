# Plan Notes

## Scope
- Stage 8 readiness bundle, self-eval, blocked evidence를 운영자가 바로 사용할 수 있는 pilot readiness pack으로 묶는다.
- `pilot evidence matrix`, `go/no-go packet`, `blocked-to-resume runbook` 문서를 추가한다.
- 현재 기준 missing env, 재실행 명령, expected artifact, go/no-go 판단 기준을 한 세트로 고정한다.
- README와 stage9 contract에 새 운영 패킷 문서 존재를 반영한다.

## Out of Scope
- sandbox/live env 실제 발급
- 외부 Redmine/Slack 운영 승인 획득
- live rehearsal 자체 재실행
- planner/runtime 기능 추가 개발

## AI-First Planner Design
- G4는 새 planner를 만드는 단계가 아니라, 이미 준비된 orchestration runtime을 운영 슬롯에 올리기 위한 release control plane 단계다.
- live readiness는 `PASS/FAIL/BLOCKED`를 그대로 유지하고, operator가 왜 blocked인지와 무엇을 채우면 되는지를 한 번에 읽어야 한다.
- 상위 agent와 인간 운영자가 같은 readiness facts를 읽도록, packet 문서는 기존 readiness bundle 결과를 canonical source로 삼아야 한다.

## Acceptance Criteria
- pilot evidence matrix 문서가 존재하고, 현재 증적/부족 증적/재실행 명령이 표로 정리된다.
- go/no-go packet 문서가 존재하고, 현재 상태가 `BLOCKED`인 이유와 go/no-go 판단 규칙이 고정된다.
- blocked-to-resume runbook 문서가 존재하고, env handoff → QA worktree 이동 → bundle 재실행 → 결과 판정 절차가 단계별로 정리된다.
- README가 새 readiness packet 문서를 링크한다.
- `tests.test_stage9_contract`와 `bash scripts/run_dev_qa_cycle.sh 9`가 통과한다.

## Risks
- 문서가 기존 readiness guide/bundle과 다른 용어를 쓰면 운영자가 판단 기준을 혼동할 수 있다.
- env checklist가 현재 external dependency와 어긋나면 잘못된 handoff를 유도할 수 있다.
- go/no-go packet이 BLOCKED와 FAIL을 섞어 쓰면 운영 리스크가 왜곡된다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage9-w1-005`
- `bash scripts/run_micro_cycle.sh gate-review stage9-w1-005`
- `python3 -m unittest tests.test_stage9_contract`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_micro_cycle.sh run stage9-w1-005 9`
