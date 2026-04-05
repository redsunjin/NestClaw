# Review Notes

## Security / Policy Review
- external env handoff 문서는 secret을 저장하는 저장소가 아니라, 어떤 값이 필요한지와 누가 채워야 하는지를 고정하는 profile이어야 한다.
- `NEWCLAW_REDMINE_MCP_TOKEN` 같은 secret은 template에 빈 값으로만 남기고, markdown 예시 본문에는 실제 값이나 길이 힌트를 남기지 않는 편이 맞다.
- validator는 required env 누락을 `BLOCKED`로 분류하되, recommended env 누락을 `FAIL`처럼 과장하지 않아야 운영 커뮤니케이션이 흔들리지 않는다.

## Architecture / Workflow Review
- canonical handoff profile은 readiness bundle, rerun status, go/no-go packet, blocked-to-resumed runbook과 같은 vocabulary를 써야 한다.
- validator는 새 판단 체계를 만들기보다, `run_stage8_readiness_bundle.sh`가 요구하는 required env 5개를 재현 가능하게 preflight 하는 얇은 계층으로 두는 편이 적절하다.
- template, profile, validator, runbook이 서로 다른 env 목록을 갖지 않도록 한 기준 문서에서 다른 절차 문서로 링크를 거는 구조가 필요하다.

## QA Gate Review
- `tests.test_stage11_contract`는 canonical profile, template, cycle integration, stage11 unit state를 함께 고정해야 한다.
- lightweight validator는 shell script smoke test로 `BLOCKED`와 `READY` 두 경로를 확인하는 편이 충분하다.
- stage11 cycle은 env-gated Stage 8 skip과 별개로, 새 profile/validator 자체는 독립적으로 PASS해야 한다.

## Review Verdict
- 진행 승인.
- 이번 단계는 external env handoff profile, secure template, lightweight validator, contract/smoke hardening 범위로 제한한다.
