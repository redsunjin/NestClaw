# Implement Notes

## Changed Files
- [x] `app/provider_invoker.py`
  - summary path용 provider invocation layer 추가
  - `lmstudio`, `ollama`, `openai-compatible api` 호출과 safe fallback 구현
- [x] `app/main.py`
  - meeting summary 실행 경로에 provider invocation 연결
  - `MODEL_PROVIDER_INVOKED` 이벤트 및 `provider_invocation` provenance 기록 추가
- [x] `app/services/orchestration_service.py`
  - status payload에 `provider_invocation` 포함
- [x] `tests/test_provider_invoker_contract.py`
  - fallback/live invocation 계약 검증 추가
- [x] `tests/test_provider_invoker_runtime.py`
  - API 경로에서 fallback/live provenance 검증 추가
- [x] `tests/test_model_registry_runtime.py`
  - summary status/events에 provider invocation 정보가 남는지 검증 보강
- [x] `tests/test_stage8_contract.py`
  - provider invoker 자산 및 wiring 정적 계약 추가
- [x] `scripts/run_dev_qa_cycle.sh`
  - stage8 provider invoker contract/runtime checks 추가
- [x] `README.md`, `TASKS.md`, `NEXT_STAGE_PLAN_2026-02-24.md`, `API_CONTRACT.md`, `AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md`
  - provider invocation 현황과 다음 단계 반영

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `app/provider_invoker.py`
  - `app/main.py`
  - `app/services/orchestration_service.py`
  - `tests/test_provider_invoker_contract.py`
  - `tests/test_provider_invoker_runtime.py`
  - `tests/test_model_registry_runtime.py`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_provider_invoker_contract tests.test_stage8_contract`
  - `env PATH="/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- 현재 live invocation은 `meeting_summary` path에만 적용했고, incident/provider 확장은 아직 남아 있다.
- `api_general` provider를 로컬에서 시험하려면 `NEWCLAW_OPENAI_BASE_URL`을 local OpenAI-compatible endpoint로 넘겨야 한다.
- provider 출력 포맷이 요구 섹션을 만족하지 않으면 fallback으로 내려가므로, live 품질보다 안정성을 우선한다.
