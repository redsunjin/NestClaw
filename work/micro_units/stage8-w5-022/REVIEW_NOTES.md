# Review Notes

## Security / Policy Review
- 단일 화면도 기존 auth header 모델과 role 경계를 그대로 유지해야 한다.
- requester는 approval detail/action을 직접 수행할 수 없고, approver/admin만 approval 처리 가능해야 한다.
- workflow automation wrapper는 기존 게이트를 우회하지 않고 `run_micro_cycle.sh`를 호출하는 얇은 오케스트레이터여야 한다.

## Architecture / Workflow Review
- 상위 운영 프로토콜은 기존 `MICRO_AGENT_WORKFLOW.md`를 대체하지 말고 그 위에 선언형 문서로 두는 편이 맞다.
- root는 simple entry, `/console`은 advanced console로 나누면 제품 진입성과 기존 운영 도구를 동시에 보존할 수 있다.
- 단일 화면은 별도 static asset으로 두고, advanced console 자산은 그대로 재사용하지 않는 편이 유지보수가 쉽다.

## QA Gate Review
- root quickstart smoke와 `/console` route smoke가 필요하다.
- expert workflow doc/script 존재와 핵심 명령이 stage8 contract로 고정돼야 한다.
- runtime smoke는 simple entry submit -> status/report path -> approval path를 다시 확인해야 한다.

## Review Verdict
- Proceed. 이번 단계는 사용성 문제와 운영 절차 문제를 동시에 정리하는 적절한 묶음이다.
