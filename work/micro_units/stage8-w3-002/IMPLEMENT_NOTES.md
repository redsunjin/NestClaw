# Implement Notes

## Changed Files
- [x] `app/incident_policy.py`
  - incident 위험도 분류표와 정책 차단 패턴을 전용 모듈로 분리
  - `IncidentPolicyDecision`과 reason message 규칙 추가
- [x] `app/main.py`
  - incident policy 평가를 새 모듈에 위임
  - approval queue에 `reason_message`, `approver_group`, `review_recommendation` 저장 지원
- [x] `tests/test_incident_policy_gate.py`
  - low/medium/high/critical, 근거 누락, 정책 차단, 승인 우회 시나리오 단위 테스트 추가
- [x] `tests/test_stage8_contract.py`
  - G3 asset 존재 여부를 Stage 8 static contract에 연결

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `app/incident_policy.py`
  - `app/main.py`
  - `tests/test_incident_policy_gate.py`
  - `tests/test_stage8_contract.py`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_stage8_contract tests.test_incident_adapter_contract`
  - `python3 -m unittest tests.test_incident_policy_gate`

## Known Risks
- `review_recommendation`은 현재 approval payload 증적이며 실제 다중승인 enforcement는 아니다.
- policy block은 문자열 패턴 기반이라 더 정교한 컨텍스트 분류가 필요할 수 있다.
- Stage 8 전체 readiness는 여전히 G4와 sandbox 증적에 의해 제한된다.
