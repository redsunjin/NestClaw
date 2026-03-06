# Review Notes

## Security / Policy Review
- sandbox rehearsal은 기본적으로 opt-in 환경변수로만 실행 가능해야 한다.
- sandbox target metadata가 없으면 `SKIP`로 종료하고 거짓 PASS를 만들지 않아야 한다.
- G4 판정은 report 존재 여부만 보지 말고 `PASS` 상태까지 확인해야 한다.
- CI에 추가되는 rehearsal step은 비밀값 부재 시 graceful skip이어야 한다.

## Architecture / Workflow Review
- G4는 Stage 8의 테스트/문서/리포트 산출물을 CI와 self-eval 양쪽에서 동일 기준으로 보게 만드는 작업이다.
- `run_dev_qa_cycle.sh`는 Stage 8 자산을 종합하는 중앙 게이트로 유지한다.
- `run_stage8_sandbox_e2e.sh`는 rehearsal 증적 생성 전용으로 유지하고 live execution 책임은 가지지 않는다.
- self-eval의 G4는 workflow wiring + PASS report 두 조건이 모두 만족될 때만 PASS가 되어야 한다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_stage8_contract tests.test_incident_policy_gate tests.test_incident_adapter_contract`
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w4-001 8`
- QA worktree에서 runtime deps가 있는 경우 `bash scripts/run_stage8_self_eval.sh` 재실행으로 G4 상태를 확인한다.

## Review Verdict
- 조건부 승인 (Approved with External Dependency Guard)
- 조건:
  1. sandbox report가 `SKIP`일 때 G4를 PASS로 올리면 안 된다.
  2. CI workflow는 Stage 8 gate를 명시적으로 포함해야 한다.
  3. rehearsal script는 외부 env 부재 시 실패 대신 SKIP로 처리해야 한다.
