# Review Notes

## Security / Policy Review
- Console은 승인 정책을 우회하지 않고 기존 API를 그대로 호출해야 한다.
- draft 적용은 기존 approver/admin 권한 검사를 그대로 사용해야 한다.
- 브라우저에는 민감 토큰을 저장하지 않고 개발용 호환 헤더만 사용한다.

## Architecture / Workflow Review
- FastAPI route는 HTML/정적 asset adapter만 추가하고 orchestration core는 수정하지 않는 것이 맞다.
- UI 상태는 클라이언트 측 fetch로 처리하고, 서버는 기존 tool catalog/draft service를 재사용한다.
- root route와 static mount만 추가해 최소 operator UI 요구를 닫는다.

## QA Gate Review
- root HTML 반환 smoke와 static asset 서빙 smoke가 필요하다.
- Stage 8 계약 테스트에 UI asset/route 존재를 고정해야 한다.
- canonical QA cycle까지 다시 통과해야 한다.

## Review Verdict
- Proceed. 범위는 최소 console 1장으로 제한하고, auth/approval 정책은 기존 API 계층에 그대로 위임한다.
