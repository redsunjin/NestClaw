# Implement Notes

## Changed Files
- [x] `app/main.py`
  - `agent submit/status/events` facade 추가
  - 규칙 기반 `task`/`incident` 라우터 및 공용 status/events payload helper 추가
  - 기존 `/task/*`, `/incident/*` 엔드포인트는 유지하고 내부 payload builder만 공용화
- [x] `app/cli.py`
  - task 전용 메뉴를 `agent submit -> status -> events -> result` 흐름으로 교체
  - incident 입력 시 필요한 최소 metadata와 run_mode 선택을 한 곳에서 받도록 정리
- [x] `tests/test_agent_entrypoint_smoke.py`
  - agent facade가 task/incident를 단일 경로로 생성/실행/조회하는 runtime smoke 추가
- [x] `tests/test_spec_contract.py`
  - `agent_submit`, `agent_status`, `agent_events` 계약 고정
- [x] `tests/test_stage8_contract.py`
  - Stage 8 cycle에 agent facade smoke가 포함되는지 계약 고정
- [x] `scripts/run_dev_qa_cycle.sh`
  - Stage 8 QA cycle에 `tests.test_agent_entrypoint_smoke` optional smoke 추가
- [x] `API_CONTRACT.md`
  - 단일 agent 진입점 계약 추가
- [x] `README.md`
  - 기본 사용자 진입점을 `agent submit/status/events`로 갱신
- [x] `TASKS.md`
  - 단일 agent facade/CLI 통합 작업 완료 상태 반영
- [x] `work/micro_units/stage8-w5-002/*`
  - plan/review/implement/evaluate 증적 정리

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `app/main.py`
  - `app/cli.py`
  - `tests/test_agent_entrypoint_smoke.py`
  - `tests/test_spec_contract.py`
  - `tests/test_stage8_contract.py`
  - `scripts/run_dev_qa_cycle.sh`
  - `API_CONTRACT.md`
  - `README.md`
  - `TASKS.md`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- 라우터는 규칙 기반이므로 free-form 요청에서 `task`/`incident` 오분류 가능성이 남아 있다.
- 현재 단일 진입점은 facade일 뿐이며 실제 LLM intent classification이나 tool planning은 아직 연결되지 않았다.
- feature worktree에는 fastapi runtime dependency가 없어 agent runtime smoke가 `SKIP`될 수 있다.
- CLI는 단일 진입점으로 정리됐지만 아직 GUI 콘솔이나 대화형 agent shell 수준은 아니다.
