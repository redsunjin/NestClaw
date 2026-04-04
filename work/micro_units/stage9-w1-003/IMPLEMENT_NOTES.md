# Implement Notes

## Changed Files
- [x] `app/agent_planner.py`
  - incident planner prompt, action normalization, deterministic fallback, provider-backed planning method를 추가했다.
- [x] `configs/model_registry.yaml`
  - incident planner routing rule(`incident_plan_actions -> local_lmstudio`)를 추가했다.
- [x] `app/main.py`
  - incident planned action 생성 경로를 planner decision 기반으로 바꾸고, planner rationale을 ticket/slack payload와 incident report에 반영했다.
  - incident planning fallback event를 status/event rail에 연결했다.
- [x] `app/services/capability_manifest_service.py`
  - incident workflow 상태를 `AI planner + deterministic fallback`으로 갱신했다.
- [x] `README.md`
  - 현재 제품 위치 설명을 incident AI planner baseline 반영 기준으로 갱신했다.
- [x] `NESTCLAW_CAPABILITY_MANIFEST.md`
  - incident workflow family 설명과 known constraints를 새 baseline에 맞게 정리했다.
- [x] `tests/test_model_registry_contract.py`
  - incident planner routing rule을 contract로 고정했다.
- [x] `tests/test_agent_planner_contract.py`
  - incident planner disabled/llm success contract를 추가했다.
- [x] `tests/test_incident_runtime_smoke.py`
  - deterministic fallback smoke와 llm success smoke를 추가/갱신했다.
- [x] `tests/test_stage9_contract.py`
  - stage9-w1-003 초기화와 campaign 진행 상태를 contract에 반영했다.

## Rollback Plan
- planner rollback 대상:
  - `app/agent_planner.py`
  - `configs/model_registry.yaml`
  - `app/main.py`
  - `app/services/capability_manifest_service.py`
- contract/doc rollback 대상:
  - `README.md`
  - `NESTCLAW_CAPABILITY_MANIFEST.md`
  - `tests/test_model_registry_contract.py`
  - `tests/test_agent_planner_contract.py`
  - `tests/test_incident_runtime_smoke.py`
  - `tests/test_stage9_contract.py`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_agent_planner_contract tests.test_model_registry_contract tests.test_stage8_contract tests.test_stage9_contract`
  - `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_agent_planner_contract tests.test_model_registry_contract tests.test_incident_runtime_smoke tests.test_model_registry_runtime`
  - `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`

## Known Risks
- incident AI planner는 아직 ticket/slack 범위의 제한된 tool set만 다루므로 broader incident sequencing까지 커버하지 않는다.
- planner rationale을 payload/report에 노출하기 시작했으므로, 이후 민감도 기준이 바뀌면 rationale redaction 정책도 함께 검토해야 한다.
- workflow-level `provider_selection`과 planner-level `planning_provenance.provider_selection`이 공존하므로 operator/documentation에서 두 필드의 의미를 계속 구분해줘야 한다.
