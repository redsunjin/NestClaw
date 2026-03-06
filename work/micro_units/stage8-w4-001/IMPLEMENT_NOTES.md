# Implement Notes

## Changed Files
- [x] `.github/workflows/quality-gate.yml`
  - Stage 8 cycle, policy gate test, sandbox rehearsal, self-eval 단계를 CI에 연결
- [x] `scripts/run_dev_qa_cycle.sh`
  - Stage 8 check에 policy gate test와 sandbox rehearsal optional check 추가
- [x] `scripts/run_stage8_self_eval.sh`
  - G4가 sandbox report의 `PASS` 상태까지 확인하도록 보강
- [x] `scripts/run_stage8_sandbox_e2e.sh`
  - sandbox rehearsal report 생성 및 env-gated SKIP(10) 처리 스크립트 추가
- [x] `tests/test_stage8_contract.py`
  - G4 asset/CI wiring/static 조건 검증 추가

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `.github/workflows/quality-gate.yml`
  - `scripts/run_dev_qa_cycle.sh`
  - `scripts/run_stage8_self_eval.sh`
  - `scripts/run_stage8_sandbox_e2e.sh`
  - `tests/test_stage8_contract.py`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_stage8_contract`
  - `bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- 실제 sandbox credential이 없으면 rehearsal은 `SKIP`만 생성한다.
- CI는 Stage 8까지 인식하지만 G4 전체 PASS는 외부 환경 의존성이 남는다.
- sandbox rehearsal은 readiness 증적이며 live incident lifecycle 보장은 아직 아니다.
