# Review Notes

## Security / Policy Review
- 브라우저 UI는 기존 auth 헤더 모델을 그대로 써야 하고 승인/권한을 우회하면 안 된다.
- 기본 예시는 모두 dry-run 또는 low-risk 시나리오여야 한다.
- output 패널에는 서버 응답만 보여주고 민감 토큰 저장은 하지 않는다.

## Architecture / Workflow Review
- 변경은 static asset에 집중하고 backend는 기존 agent facade를 그대로 재사용하는 것이 맞다.
- 사용자가 “무엇을 할 수 있는가”를 느끼게 하려면 도구 카탈로그보다 agent submit/status가 화면 상단에 와야 한다.
- 예시 데이터는 console에서만 유지하고 persisted server state와 분리한다.

## QA Gate Review
- root HTML과 static JS smoke는 agent submit/status/events 호출 문자열을 포함해야 한다.
- 기존 agent runtime smoke와 함께 다시 돌아야 한다.
- canonical QA cycle에서 web console 추가가 runtime smoke를 깨지 않는지 확인해야 한다.

## Review Verdict
- Proceed. 이번 단계는 single-agent usability 개선으로 충분하며 backend contract 변경 없이 닫을 수 있다.
