# Review Notes

## Security / Policy Review
- approve/reject는 기존 approver/admin 권한 검사를 그대로 타야 한다.
- acted_by는 actor와 일치해야 하므로 UI는 `Approver ID`를 그대로 재사용한다.
- 승인필요 예시는 low-risk 외부전송 승인 요청으로 제한해 destructive action을 만들지 않는다.

## Architecture / Workflow Review
- approval panel은 static console의 별도 섹션으로 두고 backend approval service를 그대로 재사용한다.
- agent submit/status와 approval list를 같은 페이지에 두는 것이 single-operator 흐름에 맞다.
- 실시간 push는 추가하지 않고 수동 refresh와 inline action만 둔다.

## QA Gate Review
- HTML/JS smoke가 approval panel과 approve/reject 호출을 포함해야 한다.
- 기존 runtime smoke가 승인 흐름을 이미 검증하므로 이와 함께 깨지지 않는지만 보면 된다.
- canonical QA cycle과 실제 서버 수동 검증이 필요하다.

## Review Verdict
- Proceed. approval queue는 현재 Web Console 다음 단계로 가장 자연스럽고, backend 변경 없이 닫을 수 있다.
