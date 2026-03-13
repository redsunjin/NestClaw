# Review Notes

## Security / Policy Review
- report preview/raw는 기존 `agent_status`와 동일하게 requester/reviewer/approver/admin 권한 경계를 유지해야 한다.
- report path는 `reports/` root 아래로 제한해야 하고, task result에 저장된 임의 경로를 그대로 신뢰하면 안 된다.
- raw open은 browser auth header를 유지해야 하므로 JS fetch를 통해 열어야 한다.

## Architecture / Workflow Review
- report access는 service layer에서 `task lookup -> authorize -> path resolve`를 공통화하는 것이 가장 안전하다.
- Web Console은 recent task 카드와 현재 task 패널 양쪽에서 같은 report access 함수를 재사용해야 한다.
- raw report는 별도 파일 응답 route로 두고 preview는 JSON route로 분리하는 편이 단순하다.

## QA Gate Review
- requester own report preview 성공 테스트 필요
- 다른 requester report preview 차단 테스트 필요
- web console smoke에 report preview buttons/endpoint 연결 여부 추가

## Review Verdict
- Proceed. G1 범위에서 결과 확인 동선을 닫는 데 가장 직접적인 개선이다.
