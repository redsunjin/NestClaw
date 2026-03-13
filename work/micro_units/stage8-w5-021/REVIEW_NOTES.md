# Review Notes

## Security / Policy Review
- approval detail/history는 기존 approval list와 동일하게 `approver`, `admin`만 접근 가능해야 한다.
- comment/history 노출은 승인 작업에 직접 관여하는 역할로 제한해야 한다.
- approve/reject 후에도 resolved item detail은 감사 목적상 조회 가능해야 한다.

## Architecture / Workflow Review
- approval queue와 approval action list를 service layer에서 결합해 detail payload를 만드는 것이 가장 단순하다.
- Web Console은 approval queue 카드와 recent approval 카드에서 같은 `loadApprovalDetail()` 함수를 재사용해야 한다.
- detail panel은 approval queue 패널과 분리된 읽기 전용 요약 카드로 두는 편이 operator 입장에서 가장 명확하다.

## QA Gate Review
- approver detail 조회 성공 테스트 필요
- requester detail 조회 금지 테스트 필요
- approve/reject 후 action comment history 반영 테스트 필요

## Review Verdict
- Proceed. 현재 G1에서 남은 가시성 공백 중 approval 흐름 추적을 직접 메우는 작업이다.
