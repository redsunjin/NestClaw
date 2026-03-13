# Implement Notes

## Changed Files
- `EXPERT_AGENT_OPERATING_PROTOCOL_2026-03-13.md`
  - 전문가 에이전트 작업방식과 단계/역할/자동화 규칙을 선언한다.
- `scripts/run_expert_agent_workflow.sh`
  - MWU 현재 단계, 다음 담당자, verify 흐름을 자동으로 보여주는 wrapper를 추가한다.
- `app/main.py`
  - root(`/`)를 quickstart로 바꾸고 `/console`에 기존 advanced console을 유지한다.
- `app/static/agent-quickstart.html`
  - 한 칸 입력 중심의 단일 사용 화면을 추가한다.
- `app/static/agent-quickstart.js`
  - quickstart submit/status/report/approval/recent 흐름을 구현한다.
- `app/static/agent-quickstart.css`
  - quickstart 전용 레이아웃과 카드 스타일을 추가한다.
- `README.md`, `TASKS.md`
  - quickstart와 전문가 workflow wrapper를 기준 문서에 반영한다.
- `tests/test_web_console_runtime.py`, `tests/test_stage8_contract.py`
  - root quickstart, `/console`, protocol/wrapper 존재를 회귀 테스트로 고정한다.

## Rollback Plan
- root route를 다시 기존 advanced console로 되돌리고 `/console` route를 제거한다.
- quickstart static asset 3개를 제거한다.
- 전문가 운영 프로토콜 문서와 wrapper script를 제거하고 기존 `MICRO_AGENT_WORKFLOW.md`만 유지한다.

## Known Risks
- quickstart는 metadata 없이 요청을 보내므로 복잡한 정형 입력이 필요한 future workflow에는 한계가 있다.
- wrapper script는 역할/순서를 강제하지만 노트 내용을 자동 생성하지는 않는다.
- root를 quickstart로 바꾸면서 기존 사용자가 `/console`로 이동해야 하므로 문서 링크가 충분히 유지되어야 한다.
