# Evaluate Notes

## QA Result Summary
- feature worktree 대상 테스트 통과:
  - `python3 -m unittest tests.test_web_console_runtime tests.test_agent_entrypoint_smoke tests.test_runtime_smoke tests.test_stage8_contract`
  - 결과: `51 tests`, `OK (skipped=15)`
- feature worktree micro-cycle 통과:
  - `work/micro_units/stage8-w5-022/reports/evaluate-gate-20260313T122614Z.md`
  - feature cycle report: `reports/qa/cycle-20260313T122614Z.md`
- QA worktree canonical cycle 통과:
  - `reports/qa/cycle-20260313T122703Z.md`
- wrapper script 확인:
  - `bash scripts/run_expert_agent_workflow.sh status stage8-w5-022 8`
  - `A09 Release Sync` next owner와 status report 출력 정상 확인
- 실제 UI/런타임 확인:
  - `curl -s http://127.0.0.1:8000/health` -> `{"status":"ok"}`
  - `curl -s http://127.0.0.1:8000/ | rg -n "NestClaw Quickstart|한 칸으로 시작하는 실행 에이전트"` 확인
  - `curl -s http://127.0.0.1:8000/console | rg -n "NestClaw Web Console|도구 카탈로그|승인 상세 / 이력"` 확인
- quickstart 승인 흐름 확인:
  - `POST /api/v1/agent/submit`
  - 요청: `회의 내용을 정리하고 외부 전송 승인까지 올려줘`
  - 결과: `status=NEEDS_HUMAN_APPROVAL`, `approval_queue_id=aq_0a7d3b6144774bf4aa312136f51120ab`

## Skip/Failure Reasons
- 현재 MWU 범위에서 기능 실패 없음.
- Stage 8 전체 기준의 `G4`는 여전히 sandbox/live env 미설정 시 `SKIP/PENDING`이 될 수 있다. 이는 이번 quickstart/protocol 작업과는 별개다.
- 이전 수동 병렬 스트레스 세션에서는 SQLite 손상 흔적이 있었지만, 이번 fresh DB 수동 검증과 canonical QA에서는 재현되지 않았다.

## Next Action
- 다음 작업은 quickstart 화면의 auto-refresh 토글 추가다.
- 그 다음은 planner provenance를 quickstart/current task 패널에 노출하는 작업이다.
- 운영 프로토콜 측면에서는 `scripts/run_expert_agent_workflow.sh prepare/status/verify`를 다음 MWU에도 같은 방식으로 재사용한다.
