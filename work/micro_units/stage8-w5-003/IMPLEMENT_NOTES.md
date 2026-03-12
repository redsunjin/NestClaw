# Implement Notes

## Changed Files
- [x] `app/services/__init__.py`
- [x] `app/services/orchestration_service.py`
  - agent/task/incident create/run/status/events orchestration service 추가
  - request 해석, auto routing, status payload, event payload를 FastAPI handler에서 분리
- [x] `app/main.py`
  - route handler를 service adapter 중심 구조로 축소
  - `ORCHESTRATION_SERVICE` / `OrchestrationServiceDeps` wiring 추가
- [x] `README.md`
  - 서비스 계층 분리와 현재 내부 구조 설명 추가
- [x] `TASKS.md`
  - Agent Tool Surface Follow-up 중 서비스 계층 분리 항목 완료 반영
- [x] `tests/test_stage8_contract.py`
  - service layer 파일 존재 및 `ORCHESTRATION_SERVICE` wiring 계약 추가
- [x] `work/micro_units/stage8-w5-003/*`
  - MWU plan/review/implement/evaluate 자산 추가

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `app/services/__init__.py`
  - `app/services/orchestration_service.py`
  - `app/main.py`
  - `README.md`
  - `TASKS.md`
  - `tests/test_stage8_contract.py`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- service 계층이 아직 persistence/auth helper callback을 main.py에서 주입받는 구조라 완전한 독립 계층은 아니다.
- approval endpoint와 pipeline worker는 이번 단위에서 여전히 `app/main.py`에 남아 있다.
- feature worktree에서는 runtime dependency 부재로 실제 runtime smoke가 `SKIP`될 수 있다.
