# Implement Notes

## Changed Files
- [x] `NESTCLAW_PILOT_EVIDENCE_MATRIX_2026-04-05.md`
  - 현재 확보된 회귀/readiness/self-eval/blocker 증적을 pilot 판단용 matrix로 묶었다.
- [x] `NESTCLAW_PILOT_GO_NO_GO_PACKET_2026-04-05.md`
  - 현재 권고를 `NO-GO for external live pilot / GO for internal dry-run`으로 고정하고 재판정 규칙을 적었다.
- [x] `STAGE8_BLOCKED_TO_RESUMED_RUNBOOK_2026-04-05.md`
  - 외부 env handoff 이후 QA worktree에서 readiness bundle을 재실행하는 절차를 단계별로 정리했다.
- [x] `README.md`
  - readiness guide/bundle 옆에 새 pilot packet 문서 링크를 추가했다.
- [x] `NEXT_WORK_GROUPS_2026-03-17.md`
  - current focus를 Stage 8 live-readiness resume 또는 다음 campaign 정의로 갱신했다.
- [x] `work/priority_campaigns/stage9-priority-campaign/campaign.json`
  - `g4-pilot-readiness-pack`을 활성 작업으로 올렸다.

## Rollback Plan
- 문서 rollback 대상:
  - `NESTCLAW_PILOT_EVIDENCE_MATRIX_2026-04-05.md`
  - `NESTCLAW_PILOT_GO_NO_GO_PACKET_2026-04-05.md`
  - `STAGE8_BLOCKED_TO_RESUMED_RUNBOOK_2026-04-05.md`
  - `README.md`
  - `NEXT_WORK_GROUPS_2026-03-17.md`
  - `work/priority_campaigns/stage9-priority-campaign/campaign.json`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_stage9_contract`
  - `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`

## Known Risks
- 문서 기준선은 최신 report path에 의존하므로, 새 PASS evidence가 생기면 packet도 함께 갱신해야 한다.
- go/no-go packet이 운영 현실보다 앞서가면 live pilot을 너무 빨리 열게 만들 수 있다.
- readiness bundle과 packet 문서가 다른 wording을 쓰기 시작하면 operator handoff가 다시 흔들릴 수 있다.
