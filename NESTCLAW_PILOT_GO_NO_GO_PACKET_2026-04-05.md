# NestClaw Pilot Go / No-Go Packet

## Decision Snapshot
- 문서 기준일: `2026-04-05`
- 제품 posture: `closed orchestration runtime + operator dashboard`
- 현재 권고: `NO-GO for external live pilot`
- 예외 권고: `GO for internal dry-run / operator walkthrough`

## Why It Is No-Go Today
1. Stage 8 readiness bundle 최신 결과가 `BLOCKED`다.
2. 외부 env 5개가 비어 있어 sandbox/live rehearsal을 실제로 닫을 수 없다.
3. QA rerun에서 local DB 손상과 stale worktree 문제는 정리됐고, 현재 blocker는 다시 `운영 입력 부재`로 수렴했다.

근거 문서:
- `reports/qa/cycle-20260404T153334Z.md`
- `STAGE8_QA_RERUN_STATUS_2026-04-05.md`
- `/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/stage8-readiness-bundle-20260405T034720Z.md`
- `/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/stage8-self-eval-20260405T034720Z.md`

## What Is Already Ready
- Stage 9 기준 회귀는 PASS다.
- task/incident 공통 planner-executor helper가 정리됐다.
- incident AI planner baseline과 deterministic fallback이 존재한다.
- operator dashboard는 planner rationale, action rail, execution detail을 읽을 수 있다.

## Required Inputs Before Reconsidering
- `NEWCLAW_STAGE8_SANDBOX_ENABLED=1`
- `NEWCLAW_STAGE8_SANDBOX_BASE_URL=<sandbox base url>`
- `NEWCLAW_STAGE8_SANDBOX_PROJECT=<sandbox project>`
- `NEWCLAW_STAGE8_LIVE_ENABLED=1`
- `NEWCLAW_REDMINE_MCP_ENDPOINT=<live mcp endpoint>`

필요 시 함께 준비:
- `NEWCLAW_REDMINE_MCP_TOKEN`
- `NEWCLAW_STAGE8_SANDBOX_ASSIGNEE`
- `NEWCLAW_STAGE8_SANDBOX_TRANSITION`

## Re-Decision Rules
### Go
- 최신 `run_dev_qa_cycle.sh 9`가 PASS
- 최신 `run_stage8_readiness_bundle.sh`가 PASS
- sandbox/live report가 모두 PASS
- approver/admin 운영자에게 handoff owner가 지정됨

### Conditional Go
- 내부 dry-run session, operator UI review, agent integration rehearsal만 수행
- 외부 write/live side effect는 금지

### No-Go
- readiness bundle이 `BLOCKED`
- sandbox/live report가 `FAIL`
- required env 누락
- owner/approver가 지정되지 않음

## Operator Handoff Checklist
- env 제공 owner와 연락 채널이 지정됐는가
- sandbox project/base URL이 확인됐는가
- live MCP endpoint와 token 보관 경로가 확인됐는가
- QA worktree에서 실행할 담당자가 지정됐는가
- PASS/FAIL/BLOCKED 결과를 기록할 문서 위치가 합의됐는가

## Re-Run Command
```bash
cd /Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa
source .venv/bin/activate
bash scripts/run_stage8_readiness_bundle.sh
```

## Output To Collect
- `reports/qa/stage8-readiness-bundle-*.md`
- `reports/qa/stage8-self-eval-*.md`
- `reports/qa/stage8-sandbox-e2e-*.md`
- `reports/qa/stage8-live-rehearsal-*.md`

## Final Recommendation
- 현재는 `pilot packet ready, live slot not ready` 상태다.
- 즉, 파일럿 실행 절차는 준비됐지만 외부 운영 환경이 비어 있으므로 오늘 기준 live pilot은 열지 않는다.
