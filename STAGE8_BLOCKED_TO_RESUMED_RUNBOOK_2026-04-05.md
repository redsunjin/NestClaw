# Stage 8 Blocked-To-Resumed Runbook

## 목적
- 현재 `BLOCKED`인 Stage 8 live readiness를 외부 env handoff 이후 재탐색 없이 재개하는 절차를 고정한다.
- canonical external env profile은 `STAGE8_EXTERNAL_ENV_HANDOFF_PROFILE_2026-04-05.md`를 기준으로 사용한다.

## Current Blocked State
- 최신 canonical summary: `STAGE8_QA_RERUN_STATUS_2026-04-05.md`
- 최신 readiness bundle: `/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/stage8-readiness-bundle-20260410T131205Z.md`
- 현재 상태: `BLOCKED`
- 핵심 blocker: required env 미설정
- grouped self evaluation: `PASS`
- readiness score: `7/8 (87%)`
- 메모: QA local DB 재생성과 QA worktree fast-forward 이후 다시 확인한 상태다. 최신 QA worktree HEAD는 `da52a06`이다.

## Required Env Contract
- `NEWCLAW_STAGE8_SANDBOX_ENABLED`
- `NEWCLAW_STAGE8_SANDBOX_BASE_URL`
- `NEWCLAW_STAGE8_SANDBOX_PROJECT`
- `NEWCLAW_STAGE8_LIVE_ENABLED`
- `NEWCLAW_REDMINE_MCP_ENDPOINT`

권장 추가 env:
- `NEWCLAW_REDMINE_MCP_TOKEN`
- `NEWCLAW_REDMINE_MCP_VERIFY_TLS`
- `NEWCLAW_STAGE8_SANDBOX_ASSIGNEE`
- `NEWCLAW_STAGE8_SANDBOX_TRANSITION`
- `NEWCLAW_STAGE8_LIVE_REQUESTED_BY`

## Resume Procedure
1. 외부 운영 담당자에게 env 5개와 owner 정보를 받는다.
2. 필요하면 `STAGE8_EXTERNAL_ENV_REQUEST_KIT_2026-04-10.md`의 copy/paste 요청 메시지를 그대로 사용한다.
3. canonical template `configs/stage8_external_env.handoff.env.example`를 secure local copy로 채운다.
4. `bash scripts/validate_stage8_env_handoff.sh /path/to/filled.env`로 required env completeness를 먼저 확인한다.
5. secret/token 값은 repo에 기록하지 않고 shell/session secret store에만 넣는다.
6. QA worktree로 이동한다.
7. QA virtualenv를 활성화한다.
8. readiness bundle을 재실행한다.
9. bundle report에서 `PASS/FAIL/BLOCKED`를 판정한다.
10. `PASS`면 pilot evidence matrix와 go/no-go packet을 갱신한다.
11. `FAIL`이면 sandbox/live 개별 report를 drill-down 한다.

## Resume Command
```bash
cp configs/stage8_external_env.handoff.env.example /tmp/stage8_external_env.env
bash scripts/validate_stage8_env_handoff.sh /tmp/stage8_external_env.env

cd /Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa
source .venv/bin/activate
set -a
source /tmp/stage8_external_env.env
set +a
bash scripts/run_stage8_readiness_bundle.sh
```

## Expected Artifacts
- `reports/qa/stage8-readiness-bundle-*.md`
- `reports/qa/stage8-self-eval-*.md`
- `reports/qa/stage8-sandbox-e2e-*.md`
- `reports/qa/stage8-live-rehearsal-*.md`

## Decision Handling
### If PASS
- latest bundle report를 canonical evidence로 승격
- `NESTCLAW_PILOT_EVIDENCE_MATRIX_2026-04-05.md`를 PASS 기준으로 갱신
- `NESTCLAW_PILOT_GO_NO_GO_PACKET_2026-04-05.md`를 `GO` 또는 `Conditional Go`로 재판정

### If BLOCKED
- missing env checklist를 다시 확인
- env owner와 handoff completeness를 점검
- 코드 문제로 분류하지 않는다

### If FAIL
- sandbox/live 개별 report reason을 우선 확인
- runtime dependency, endpoint, credential, policy gate 중 어느 축인지 분리
- 필요한 경우 QA worktree가 feature 최신 HEAD와 일치하는지, local state DB가 정상인지 먼저 확인한다
- 필요한 경우 `bash scripts/run_stage8_sandbox_e2e.sh`와 `bash scripts/run_stage8_live_rehearsal.sh`를 개별 재실행한다

## Guardrails
- secret/token을 markdown 문서에 남기지 않는다.
- `BLOCKED`를 `FAIL`처럼 커뮤니케이션하지 않는다.
- `PASS` 증적 없이 live pilot을 열지 않는다.
