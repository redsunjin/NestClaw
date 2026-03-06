# Plan Notes

## Scope
- `app/main.py`에 흩어진 incident 승인 분류 로직을 별도 정책 모듈로 분리한다.
- 위험도(`low/medium/high/critical`), 근거 누락, 정책 차단 패턴을 코드 레벨 규칙으로 고정한다.
- 승인 큐에 `reason_message`, `approver_group`, `review_recommendation` 증적을 남길 수 있게 연결한다.
- `tests/test_incident_policy_gate.py`로 정책 룰 단위 테스트를 추가한다.

## Out of Scope
- 다중 승인자 실제 강제 로직
- Sandbox/실서비스 Redmine 연동
- 승인 UI/운영 알림 UX 개선
- Stage 8 CI wiring 및 Sandbox E2E 증적 확보

## Acceptance Criteria
- `tests/test_incident_policy_gate.py`가 통과한다.
- high/critical risk의 승인 필요 여부가 정책 모듈에서 일관되게 판정된다.
- 근거 누락(`missing_evidence`)과 정책 차단(`external_send_requested`)이 unit test로 고정된다.
- `app/main.py` incident 경로가 정책 모듈 판정 결과를 approval queue/event/status와 연결한다.
- `bash scripts/run_micro_cycle.sh run stage8-w3-002 8`가 통과한다.

## Risks
- 정책 모듈과 action card 스키마가 분리되며 필드명 drift 위험이 있다.
- `review_recommendation`은 현재 증적 기록만 하고 실제 2인 승인 강제는 하지 않는다.
- 차단 패턴이 단순 문자열 매칭이라 false positive가 생길 수 있다.

## Test Plan
- 단위 테스트:
  - `python3 -m unittest tests.test_incident_policy_gate`
  - `python3 -m unittest tests.test_stage8_contract tests.test_incident_adapter_contract`
- 구현 검증:
  - `env PYTHONPYCACHEPREFIX=.pycache python3 -m py_compile app/incident_policy.py app/main.py`
- 마이크로 게이트:
  - `bash scripts/run_micro_cycle.sh run stage8-w3-002 8`
