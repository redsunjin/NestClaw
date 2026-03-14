# Implement Notes

## Changed Files
- `scripts/run_stage8_readiness_bundle.sh`
- `STAGE8_RUNTIME_READINESS_GUIDE_2026-03-15.md`
- `README.md`
- `tests/test_stage8_contract.py`

## Implementation Summary
- Stage 8 self-eval, sandbox rehearsal, live rehearsal을 한 번에 실행하고 결과를 묶는 readiness bundle script를 추가했다.
- env 누락 시 missing checklist와 `BLOCKED` 상태를 한 report에 남기도록 만들었다.
- runtime readiness guide를 추가해 필요한 env와 해석 기준을 고정했다.
- README와 contract test도 새 readiness assets를 기준으로 갱신했다.

## Rollback Plan
- `scripts/run_stage8_readiness_bundle.sh`와 readiness guide를 제거하고 기존 개별 rehearsal/self-eval 실행 방식으로 되돌린다.
- README와 contract test에서 readiness bundle 관련 항목을 제거한다.

## Known Risks
- readiness bundle은 개별 script의 exit code에 의존하므로 rehearsal script의 판정 규칙이 바뀌면 같이 맞춰야 한다.
- env checklist는 현재 G4 요구사항 기준이므로 live integration 요구가 늘어나면 guide도 갱신해야 한다.
- BLOCKED는 의도된 상태지만, 외부 env가 없는 한 실제 live PASS를 대체하지는 못한다.
