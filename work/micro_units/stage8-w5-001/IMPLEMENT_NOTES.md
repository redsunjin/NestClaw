# Implement Notes

## Changed Files
- [x] `app/main.py`
  - incident runtime에 `mcp-live` 모드와 `context_dry_run` / `mcp_dry_run` 분리 추가
  - sandbox project env를 action payload에 반영
- [x] `app/incident_mcp.py`
  - env-gated Redmine MCP live HTTP bridge 추가
  - live endpoint/토큰/TLS 검증 옵션 처리
- [x] `scripts/stage8_live_rehearsal_runner.py`
  - incident create/run + Redmine lifecycle(update/comment/assign/transition) 실행 러너 추가
- [x] `scripts/run_stage8_live_rehearsal.sh`
  - live rehearsal 리포트 생성 및 `SKIP(10)`/`PASS`/`FAIL` 분기 추가
- [x] `scripts/run_dev_qa_cycle.sh`
  - Stage 8 runtime smoke/live rehearsal skip-aware 체크 추가
  - dependency-gated skip reason 출력 개선
- [x] `tests/test_incident_adapter_contract.py`
  - live HTTP bridge 계약 테스트 추가
- [x] `tests/test_incident_runtime_smoke.py`
  - `mcp-live` 실행 모드 분기 테스트 추가
- [x] `tests/test_stage8_contract.py`
  - live rehearsal 자산 및 `mcp-live` 계약 고정 테스트 추가
- [x] `STAGE8_LIVE_REHEARSAL_RUNBOOK_2026-03-07.md`
  - 환경변수, HTTP bridge 계약, 실행/롤백 절차 문서화
- [x] `README.md`
- [x] `TASKS.md`
- [x] `NEXT_STAGE_PLAN_2026-02-24.md`
  - live rehearsal follow-up 상태 반영
- [x] `work/micro_units/stage8-w5-001/*`
  - MWU plan/review/implement/evaluate 자산 추가

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `app/main.py`
  - `app/incident_mcp.py`
  - `scripts/run_stage8_live_rehearsal.sh`
  - `scripts/stage8_live_rehearsal_runner.py`
  - `scripts/run_dev_qa_cycle.sh`
  - `tests/test_incident_adapter_contract.py`
  - `tests/test_incident_runtime_smoke.py`
  - `tests/test_stage8_contract.py`
  - `STAGE8_LIVE_REHEARSAL_RUNBOOK_2026-03-07.md`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_stage8_contract tests.test_incident_adapter_contract`
  - `bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- live bridge endpoint의 실제 payload/response shape가 runbook 계약과 다르면 sandbox 연결 전에 추가 보정이 필요하다.
- 현재 feature worktree 환경에는 runtime dependency가 없어 live rehearsal과 runtime smoke가 `SKIP`된다.
- `mcp-live`는 외부 MCP만 live로 바꾸므로, 진짜 live RAG 연동까지는 보장하지 않는다.
- lifecycle follow-up 호출은 endpoint가 `issue_id` 또는 `external_ref`를 반환한다는 가정에 의존한다.
