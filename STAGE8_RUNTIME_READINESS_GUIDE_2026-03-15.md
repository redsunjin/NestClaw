# Stage 8 Runtime Readiness Guide

## 목적
- sandbox rehearsal, live rehearsal, self-eval을 한 번에 확인하는 readiness 절차를 고정한다.
- env가 없을 때는 무엇이 비어 있는지 바로 알 수 있게 한다.

## 필수 환경 변수
- `NEWCLAW_STAGE8_SANDBOX_ENABLED`
- `NEWCLAW_STAGE8_SANDBOX_BASE_URL`
- `NEWCLAW_STAGE8_SANDBOX_PROJECT`
- `NEWCLAW_STAGE8_LIVE_ENABLED`
- `NEWCLAW_REDMINE_MCP_ENDPOINT`

## 권장 추가 환경 변수
- `NEWCLAW_REDMINE_MCP_TOKEN`
- `NEWCLAW_STAGE8_SANDBOX_ASSIGNEE`
- `NEWCLAW_STAGE8_SANDBOX_TRANSITION`
- `NEWCLAW_DB_PATH`

## 실행 순서
1. `bash scripts/run_stage8_readiness_bundle.sh`
2. `reports/qa/stage8-readiness-bundle-*.md`에서 `PASS/FAIL/BLOCKED`를 확인한다.
3. `BLOCKED`면 누락된 env를 채우고 다시 실행한다.

## 해석 기준
- `PASS`: self-eval, sandbox, live rehearsal이 모두 통과했다.
- `BLOCKED`: 외부 sandbox/live metadata 또는 enable flag가 비어 있다.
- `FAIL`: 스크립트 또는 runtime이 실제로 실패했다.
