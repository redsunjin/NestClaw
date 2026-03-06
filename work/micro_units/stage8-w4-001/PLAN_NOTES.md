# Plan Notes

## Scope
- Stage 8 CI 품질게이트를 `.github/workflows/quality-gate.yml`에 통합한다.
- `scripts/run_dev_qa_cycle.sh 8`가 G3/G4 자산을 함께 검증하도록 확장한다.
- Stage 8 sandbox rehearsal 증적 스크립트를 추가해 `reports/qa/stage8-sandbox-e2e-*.md` 리포트를 생성한다.
- G4 판정이 sandbox report의 `PASS/SKIP` 상태를 구분하도록 `run_stage8_self_eval.sh`를 보강한다.

## Out of Scope
- 실제 Redmine live ticket lifecycle 실행
- CI 외부 비밀값/credential provisioning
- 운영용 sandbox 프로젝트 권한 위임 자동화
- G5 이후 파일럿 안정화 작업

## Acceptance Criteria
- `tests/test_stage8_contract.py`가 G4 자산을 포함해 통과한다.
- `.github/workflows/quality-gate.yml`가 Stage 8 gate(`run_dev_qa_cycle.sh 8`, sandbox rehearsal, self-eval)를 포함한다.
- `scripts/run_stage8_sandbox_e2e.sh`가 리포트를 생성하고, 환경 미충족 시 `SKIP(10)`를 반환한다.
- `bash scripts/run_micro_cycle.sh run stage8-w4-001 8`가 통과한다.
- G4는 sandbox report가 `PASS`가 아닐 때 `PENDING`으로 남는다.

## Risks
- CI에서 sandbox rehearsal이 환경 미충족으로 자주 `SKIP`될 수 있다.
- rehearsal script가 PASS 기준을 너무 느슨하게 가지면 G4를 과대평가할 수 있다.
- 실제 sandbox credential이 없는 상태에서는 G4 전체 PASS가 불가능할 수 있다.

## Test Plan
- 정적/단위:
  - `python3 -m unittest tests.test_stage8_contract tests.test_incident_policy_gate tests.test_incident_adapter_contract`
  - `env PYTHONPYCACHEPREFIX=.pycache python3 -m py_compile scripts/run_stage8_sandbox_e2e.sh`
- 품질게이트:
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w4-001 8`
- rehearsal:
  - `bash scripts/run_stage8_sandbox_e2e.sh` (env 미충족 시 SKIP expected)
