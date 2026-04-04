# NestClaw Pilot Evidence Matrix

## 목적
- 외부 sandbox/live env가 열렸을 때 pilot session을 시작하기 전에 어떤 증적이 이미 확보됐고, 무엇이 아직 비어 있는지 한 장에서 확인한다.
- 코드 회귀와 운영 blocker를 분리해서 판단한다.

## 현재 Snapshot
- 기준 시각: `2026-04-04T15:28:09Z` 이후 최신 report
- 현재 live pilot 판단: `NO-GO`
- 현재 내부 dry-run/demo 판단: `GO`

## Evidence Matrix
| 영역 | 현재 증적 | 상태 | 해석 | 다음 액션 |
| --- | --- | --- | --- | --- |
| Stage 9 전체 회귀 | `reports/qa/cycle-20260404T152245Z.md` | PASS | 코드/계약/런타임 회귀는 통과 | 최신 기준 유지 |
| Stage 8 readiness bundle | `reports/qa/stage8-readiness-bundle-20260404T152809Z.md` | BLOCKED | 외부 env 5개 누락으로 live readiness 판단 불가 | env handoff 후 bundle 재실행 |
| Stage 8 self evaluation | `reports/qa/stage8-self-eval-20260404T152809Z.md` | PENDING | readiness score `6/8`, sandbox/live evidence 미완료 | sandbox/live PASS 증적 확보 |
| Sandbox rehearsal | `reports/qa/stage8-sandbox-e2e-20260404T152814Z.md` | SKIP | sandbox env와 runtime dependency 미준비 | env/venv 정비 후 재실행 |
| Live rehearsal | `reports/qa/stage8-live-rehearsal-20260404T152814Z.md` | SKIP | live env와 endpoint 미준비 | env handoff 후 재실행 |
| Historical QA blocked proof | `/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/stage8-readiness-bundle-20260314T175150Z.md` | BLOCKED | QA worktree에서도 같은 blocker가 재현됨 | 동일 절차로 resume |
| Operator transparency surface | `work/micro_units/stage9-w1-004/reports/evaluate-gate-20260404T152119Z.md` | PASS | operator가 planner/action/execution trace를 읽을 수 있음 | pilot 운영면으로 유지 |

## Missing External Inputs
반드시 채워져야 하는 env:
- `NEWCLAW_STAGE8_SANDBOX_ENABLED`
- `NEWCLAW_STAGE8_SANDBOX_BASE_URL`
- `NEWCLAW_STAGE8_SANDBOX_PROJECT`
- `NEWCLAW_STAGE8_LIVE_ENABLED`
- `NEWCLAW_REDMINE_MCP_ENDPOINT`

권장 추가 env:
- `NEWCLAW_REDMINE_MCP_TOKEN`
- `NEWCLAW_STAGE8_SANDBOX_ASSIGNEE`
- `NEWCLAW_STAGE8_SANDBOX_TRANSITION`
- `NEWCLAW_DB_PATH`

## Pilot Entry Criteria
다음 네 조건이 모두 만족되면 live pilot `GO`로 전환할 수 있다.

1. `bash scripts/run_dev_qa_cycle.sh 9` 최신 report가 PASS
2. `bash scripts/run_stage8_readiness_bundle.sh` 최신 report가 `PASS`
3. sandbox rehearsal report가 `PASS`
4. live rehearsal report가 `PASS`

## Current Recommendation
- 지금은 `코드 배포 준비 완료 + 외부 운영 슬롯 미준비` 상태다.
- 따라서 내부 demo, dry-run, operator dashboard 검토는 진행 가능하다.
- 외부 sandbox/live를 사용하는 pilot session은 `NO-GO`다.
