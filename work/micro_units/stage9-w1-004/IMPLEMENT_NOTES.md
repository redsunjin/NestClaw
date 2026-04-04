# Implement Notes

## Changed Files
- [x] `app/static/agent-console.html`
  - planner signal strip, rationale card, action inspector, execution inspector slot을 추가했다.
- [x] `app/static/agent-console.js`
  - planner provenance를 signal chip/action rail/execution detail로 렌더링하는 helper를 추가했다.
  - recent task 카드에도 rationale, degraded/fallback, run mode, executed flow를 축약 노출하도록 바꿨다.
- [x] `app/static/agent-console.css`
  - signal chip, action rail, execution inspector 스타일을 operator dashboard 톤에 맞게 추가했다.
- [x] `app/static/agent-quickstart.html`
  - compact planner signal strip, rationale note, planned/executed rail 슬롯을 추가했다.
- [x] `app/static/agent-quickstart.js`
  - quickstart가 same payload contract를 compact signal/action rail vocabulary로 읽도록 확장했다.
  - recent request list에도 rationale/run mode/report readiness 요약을 추가했다.
- [x] `app/static/agent-quickstart.css`
  - quickstart용 compact signal chip/action rail 스타일과 flow grid를 추가했다.
  - 새 transparency surface에 맞춰 responsive media query를 정리했다.
- [x] `app/services/orchestration_service.py`
  - `agent.recent` payload에 `planning_rationale`, `run_mode`, executed tool 흐름을 실어 UI transparency를 위한 요약 컨텍스트를 보강했다.
- [x] `tests/test_web_console_runtime.py`
  - 새 transparency slot과 JS/CSS helper 연결을 runtime contract로 고정했다.
- [x] `tests/test_stage8_contract.py`
  - console helper 기대값을 `renderActionInspector`/`rationaleLines` 기준으로 갱신했다.
- [x] `tests/test_stage9_contract.py`
  - stage9-w1-004 초기화와 operator transparency slot을 contract에 반영했다.

## Rollback Plan
- UI rollback 대상:
  - `app/static/agent-console.html`
  - `app/static/agent-console.js`
  - `app/static/agent-console.css`
  - `app/static/agent-quickstart.html`
  - `app/static/agent-quickstart.js`
  - `app/static/agent-quickstart.css`
- payload/test rollback 대상:
  - `app/services/orchestration_service.py`
  - `tests/test_web_console_runtime.py`
  - `tests/test_stage8_contract.py`
  - `tests/test_stage9_contract.py`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_stage9_contract tests.test_web_console_runtime`
  - `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_stage8_contract tests.test_stage9_contract tests.test_planner_executor_service tests.test_web_console_runtime tests.test_capability_manifest_runtime tests.test_incident_runtime_smoke`
  - `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`

## Known Risks
- planner rationale를 더 드러내면서 quickstart가 다시 과밀해질 수 있어, 이후 copy 추가 시 chip/rail 밀도 상한을 지켜야 한다.
- action rail은 payload contract 재사용에 의존하므로, planned action schema가 바뀌면 console/quickstart helper도 같이 갱신해야 한다.
- `agent.recent`에 설명 필드가 늘어난 만큼, 이후 외부 surface로 recent payload를 노출할 때 민감도 기준을 다시 점검해야 한다.
