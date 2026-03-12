# Plan Notes

## Scope
- `app/cli.py`를 menu mode와 non-interactive tool mode를 함께 지원하는 구조로 개편한다.
- tool mode에 `submit`, `status`, `events`, `approve`, `reject` 명령을 추가한다.
- tool mode는 `--json` 출력과 명시적 exit code를 지원한다.
- agent submit/status/events와 approval approve/reject 흐름이 HTTP wrapper가 아니라 in-process service/application 호출로 동작하도록 정리한다.
- CLI 사용법과 backlog 문서를 업데이트하고, runtime smoke 테스트를 추가한다.

## Out of Scope
- MCP server 구현
- 실제 LLM intent routing 연결
- operator UI 추가
- live sandbox credential을 요구하는 rehearsal 실행
- approval list 명령의 고도화 필터링 UX

## Acceptance Criteria
- `python3 app/cli.py submit ... --json`이 agent task/incident를 생성하고 JSON을 반환한다.
- `python3 app/cli.py status --task-id ... --json`과 `events --task-id ... --json`이 동작한다.
- `python3 app/cli.py approve ... --json`, `reject ... --json`이 approval queue를 직접 처리한다.
- 기존 메뉴형 CLI 기본 흐름은 유지된다.
- CLI는 서비스 계층 또는 같은 application 코어를 직접 호출하며, 로컬 HTTP 호출에 의존하지 않는다.
- 관련 smoke/contract 테스트와 `bash scripts/run_micro_cycle.sh run stage8-w5-004 8`가 통과한다.

## Risks
- 메뉴형 UX와 명령형 UX를 한 파일에 같이 두면 진입점 분기 버그가 생길 수 있다.
- CLI가 FastAPI route 함수나 global runtime 상태에 과도하게 결합되면 MCP 확장성이 약해질 수 있다.
- approval 처리에서 actor identity/role 검증을 잘못 연결하면 권한 회귀가 생길 수 있다.

## Test Plan
- 정적:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
- 런타임:
  - `python3 -m unittest tests.test_agent_entrypoint_smoke tests.test_incident_runtime_smoke tests.test_tool_cli_smoke`
- 품질 게이트:
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-004 8`
