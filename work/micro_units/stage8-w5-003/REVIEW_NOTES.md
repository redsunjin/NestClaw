# Review Notes

## Security / Policy Review
- service 계층 분리 후에도 기존 `_authorize`, `_authorize_task_access`, `_ensure_workflow`를 그대로 재사용해야 한다.
- service가 approval/RBAC/idempotency를 우회하는 별도 경로를 만들면 안 된다.
- CLI/MCP 재사용을 염두에 두더라도 actor context는 항상 명시적으로 전달되어야 한다.

## Architecture / Workflow Review
- 현재 핵심 병목은 orchestration 로직이 `app/main.py` FastAPI handler 안에 뭉쳐 있다는 점이다.
- 이번 단위는 새 기능 추가보다 `FastAPI -> service adapter` 구조를 만드는 인프라 작업이다.
- service는 HTTP에 종속되지 않아야 하며, route handler는 request validation과 dependency injection만 담당하는 것이 맞다.
- pipeline worker와 persistence/auth helper는 이번 단위에서 main.py에 남겨도 된다. 우선 CRUD/agent facade 경계만 정리한다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `python3 -m unittest tests.test_runtime_smoke tests.test_agent_entrypoint_smoke tests.test_incident_runtime_smoke`
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-003 8`
- QA worktree에서는 기존 `.venv`로 runtime smoke와 browser smoke를 다시 확인한다.

## Review Verdict
- 조건부 승인 (Approved as Service Extraction First)
- 조건:
  1. `/agent/*`, `/task/*`, `/incident/*`의 외부 계약은 유지할 것
  2. service 분리 후에도 auth/policy/idempotency 흐름은 기존 helper를 재사용할 것
  3. 이번 단위에서 MCP/CLI 확장까지 욕심내지 말고 재사용 가능한 service 표면까지만 만들 것
