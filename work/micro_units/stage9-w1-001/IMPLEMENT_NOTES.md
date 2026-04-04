# Implement Notes

## Changed Files
- [x] `app/services/planner_executor_service.py`
  - task/incident 공통 planner snapshot, planner event emission, planned action 실행 루프, action result persistence helper 추가
  - workflow별 planner 종류와 무관하게 같은 executor rail을 재사용할 수 있게 함
- [x] `app/services/__init__.py`
  - 공통 planner/executor helper export 추가
- [x] `app/main.py`
  - task workflow가 공통 planner snapshot/event/action-result helper를 사용하도록 정리
  - incident workflow도 같은 helper를 사용하도록 정리
  - provider/action adapter 결과를 공통 최소 필드 contract로 생성하도록 정리
- [x] `tests/test_planner_executor_service.py`
  - helper 단위 테스트 추가
- [x] `tests/test_agent_planner_runtime.py`
  - task action result 최소 공통 필드 검증 추가
- [x] `tests/test_incident_runtime_smoke.py`
  - incident action result 최소 공통 필드 검증 추가
- [x] `tests/test_stage9_contract.py`
  - stage9 helper 존재 및 `run_dev_qa_cycle.sh 9` 연결 검증 추가
- [x] `scripts/run_dev_qa_cycle.sh`
  - stage9 helper 테스트를 Stage 9 QA cycle에 연결

## Rollback Plan
- 전체 롤백: `git revert 966e28a` 이후 이번 implement commit을 추가로 revert
- 부분 롤백 대상:
  - `app/services/planner_executor_service.py`
  - `app/services/__init__.py`
  - `app/main.py`
  - `tests/test_planner_executor_service.py`
  - `tests/test_agent_planner_runtime.py`
  - `tests/test_incident_runtime_smoke.py`
  - `tests/test_stage9_contract.py`
  - `scripts/run_dev_qa_cycle.sh`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_stage8_contract tests.test_stage9_contract`
  - `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_agent_planner_runtime tests.test_incident_runtime_smoke`

## Known Risks
- 공통 helper는 내부 rail만 정리한 것이므로 planner 결정 로직 자체는 여전히 task/incident별 분기다.
- `action_cards`와 `planned_actions`를 incident에서 둘 다 유지하고 있어, 후속 단계에서 중복 필드 정리가 추가로 필요할 수 있다.
- browser smoke는 여전히 Playwright session 부재 시 `SKIP` 정책에 의존하므로, 실제 브라우저 E2E 보강은 별도 운영 슬롯에서 확인해야 한다.
