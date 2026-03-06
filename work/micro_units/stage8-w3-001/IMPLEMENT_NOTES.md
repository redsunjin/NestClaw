# Implement Notes

## Changed Files
- [x] `app/main.py`
  - incident 전용 `create/run/status/events` 엔드포인트 추가
  - incident dry-run 파이프라인(`ingest -> planner -> executor -> reviewer -> reporter`) 구현
  - action card 생성, 정책 차단, 승인 큐 전환, 재시도 소진(`retry_exhausted`) 복구 경로 구현
  - approval 재개 시 workflow 타입에 따라 task/incident 파이프라인을 분기하도록 보강
- [x] `tests/test_incident_runtime_smoke.py`
  - incident DONE, 고위험 승인대기, 정책 차단, retry_exhausted, task/incident 경로 분리 smoke test 추가
- [x] `scripts/run_dev_qa_cycle.sh`
  - Stage 8 nested cycle에서 self-eval을 건너뛸 수 있도록 `NEWCLAW_SKIP_STAGE8_SELF_EVAL` 가드 추가
- [x] `scripts/run_micro_cycle.sh`
  - Stage 8 evaluate gate가 내부 `run_dev_qa_cycle.sh 8` 호출 시 self-eval 재귀를 피하도록 환경변수 주입
- [x] `scripts/run_stage8_self_eval.sh`
  - runtime smoke가 `SKIP`되면 G2를 `PASS` 대신 `PENDING`으로 남기도록 판정 보강
- [x] `tests/test_stage8_contract.py`
  - incident runtime smoke 자산 존재 여부와 self-eval 재귀 방지 문자열 검증 추가

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 시 우선 복원 대상:
  - `app/main.py`
  - `tests/test_incident_runtime_smoke.py`
  - `scripts/run_dev_qa_cycle.sh`
  - `scripts/run_micro_cycle.sh`
  - `scripts/run_stage8_self_eval.sh`
  - `tests/test_stage8_contract.py`
- 롤백 후 확인 명령:
  - `python3 -m unittest tests.test_stage8_contract tests.test_incident_adapter_contract`
  - `env NEWCLAW_SKIP_STAGE8_SELF_EVAL=1 bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- 기본 `python3` 환경에는 `fastapi`가 없어 runtime smoke가 `SKIP`될 수 있다.
- incident runtime은 현재 dry-run 전용이며 live adapter 연동은 별도 MWU에서 다뤄야 한다.
- task/incident가 approval queue를 공유하므로 향후 정책 분류 확장 시 reason code 충돌을 주의해야 한다.
