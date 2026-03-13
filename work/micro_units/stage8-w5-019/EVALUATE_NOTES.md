# Evaluate Notes

## QA Result Summary
- feature worktree 대상 테스트 통과:
  - `python3 -m unittest tests.test_web_console_runtime tests.test_agent_entrypoint_smoke tests.test_stage8_contract`
  - 결과: `41 tests`, `OK (skipped=6)`
- feature worktree micro-cycle 통과:
  - `bash scripts/run_micro_cycle.sh run stage8-w5-019 8`
  - evaluate gate report: `work/micro_units/stage8-w5-019/reports/evaluate-gate-20260313T091909Z.md`
  - cycle report: `reports/qa/cycle-20260313T091909Z.md`
- QA worktree canonical cycle 통과:
  - cycle report: `reports/qa/cycle-20260313T092219Z.md`
  - runtime smoke, browser swagger smoke, stage8 grouped self-eval baseline 모두 PASS
- 실제 서버 확인:
  - `http://127.0.0.1:8000/` root 로딩 확인
  - `/health` 응답 확인
  - `/api/v1/agent/recent` 응답 확인
  - task 하나를 생성한 뒤 recent 목록에 즉시 반영되는 것 확인

## Skip/Failure Reasons
- feature worktree 단계에서는 skip/failure 없음.
- 첫 canonical QA 시도에서 기존 QA 서버가 점유한 DB 때문에 browser smoke가 `database is locked`로 실패했다.
- 기존 서버/프로세스를 정리하고 임시 DB 경로로 재실행한 뒤 canonical QA는 PASS했다.

## Next Action
- 다음 G1 후속으로 recent task에서 report preview/link, approval history drill-down, auto-refresh UX를 추가한다.
