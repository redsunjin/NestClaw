# Plan Notes

## Scope
- 전문가 에이전트가 `Plan -> Review -> Implement -> Evaluate -> Sync` 순서로 움직이는 상위 운영 프로토콜 문서를 선언한다.
- 기존 `run_micro_cycle.sh` 위에 상태/오너/검증 흐름을 보여주는 automation wrapper를 추가한다.
- root(`/`)를 단일 사용 진입 화면으로 바꾸고, 기존 full console은 `/console`로 이동한다.
- 단일 화면은 한 개의 자연어 입력창으로 요청 제출, 상태/보고서/승인 요약을 기본 동선으로 제공한다.

## Out of Scope
- LLM 기반 multi-step planner 고도화
- approval auto-refresh/polling 토글
- advanced console 제거

## Acceptance Criteria
- 전문가 에이전트 작업방식 문서가 저장소 기준 문서로 추가된다.
- automation wrapper가 현재 MWU의 다음 담당 단계와 verify 흐름을 제공한다.
- `/`가 단일 진입 화면을 제공하고 `/console`에서 기존 advanced console을 유지한다.
- 단일 화면만으로 요청 제출, 결과 확인, 승인 필요 시 최소 조치가 가능하다.

## Risks
- root 경로를 바꾸면 기존 web console 테스트/문서가 깨질 수 있다.
- 단일 화면이 너무 단순하면 고급 기능이 숨겨져 오히려 혼란이 생길 수 있다.
- wrapper script는 노트 내용을 자동 작성하지는 못하므로 역할을 과대포장하면 안 된다.

## Test Plan
- `python3 -m unittest tests.test_web_console_runtime tests.test_agent_entrypoint_smoke tests.test_runtime_smoke tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-022 8`
- QA worktree에서 canonical cycle과 실제 `/`, `/console`, 전문가 workflow script 확인
