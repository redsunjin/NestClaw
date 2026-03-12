# Implement Notes

## Changed Files
- [x] `app/cli.py`
  - HTTP wrapper를 제거하고 local sync service 기반 `submit/status/events/approve/reject` subcommand 추가
  - 기존 interactive menu는 기본 진입점으로 유지
- [x] `app/services/approval_service.py`
  - approval list/approve/reject 로직을 재사용 가능한 서비스로 분리
- [x] `app/services/__init__.py`
  - approval/orchestration service export 반영
- [x] `app/main.py`
  - approval route handler를 service adapter로 축소
  - async server service와 sync CLI service를 모두 만들 수 있는 builder 함수 추가
- [x] `tests/test_tool_cli_smoke.py`
  - tool CLI의 submit/status/events/approve/reject smoke 추가
- [x] `tests/test_stage8_contract.py`
  - approval service 및 non-interactive CLI contract 추가
- [x] `scripts/run_dev_qa_cycle.sh`
  - stage8 tool CLI runtime smoke를 QA cycle에 연결
- [x] `README.md`
  - local tool CLI 실행 예시 추가
- [x] `TASKS.md`
  - non-interactive tool CLI 항목 완료 반영
- [x] `NEXT_STAGE_PLAN_2026-02-24.md`
  - 다음 우선순위를 MCP server 중심으로 재정렬
- [x] `work/micro_units/stage8-w5-004/*`
  - MWU plan/review/implement/evaluate 자산 추가

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `app/cli.py`
  - `app/services/approval_service.py`
  - `app/services/__init__.py`
  - `app/main.py`
  - `tests/test_tool_cli_smoke.py`
  - `tests/test_stage8_contract.py`
  - `README.md`
  - `TASKS.md`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- CLI는 현재 local process에서 sync execution으로 동작하므로 live sandbox rehearsal 같은 장기 실행/원격 인증 흐름은 별도 MCP/HTTP 표면이 더 적합하다.
- approval service는 분리됐지만 audit summary와 일부 pipeline worker helper는 여전히 `app/main.py`에 남아 있다.
- feature worktree에서는 runtime dependency 부재로 CLI smoke가 `SKIP`될 수 있다.
