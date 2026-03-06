# Stage 8 Live Rehearsal Runbook (2026-03-07)

## 목적
Stage 8의 rehearsal-dry-run 이후 실제 외부 sandbox에 대해 `mcp-live` 검증을 수행하는 절차를 고정한다.

## 실행 범위
- Incident create/run 경로는 NestClaw 내부 API를 사용한다.
- RAG 컨텍스트 수집은 dry-run으로 유지한다.
- Redmine MCP 실행만 live mode로 전환한다.
- 검증 대상 lifecycle:
  - `issue.create`
  - `issue.update`
  - `issue.add_comment`
  - `issue.assign`
  - `issue.transition`

## 선행 조건
- QA worktree가 최신 feature 커밋으로 fast-forward 되어 있어야 한다.
- sandbox project, assignee, transition 값이 사전에 합의되어 있어야 한다.
- Redmine MCP bridge endpoint가 아래 HTTP 계약을 지원해야 한다.

요청 계약:
```json
{
  "tool": "redmine",
  "method": "issue.create",
  "payload": {"project_id": "OPS-SANDBOX"},
  "actor_context": {"actor_id": "stage8_live_runner", "actor_role": "requester"},
  "requested_at": "2026-03-07T00:00:00+00:00"
}
```

응답 계약:
```json
{
  "status": "ok",
  "external_ref": "RM-123",
  "issue_id": "RM-123",
  "message": "ticket created"
}
```

## 필수 환경변수
- `NEWCLAW_STAGE8_LIVE_ENABLED=1`
- `NEWCLAW_REDMINE_MCP_ENDPOINT=https://...`
- `NEWCLAW_STAGE8_SANDBOX_BASE_URL=https://...`
- `NEWCLAW_STAGE8_SANDBOX_PROJECT=OPS-SANDBOX`

## 권장 환경변수
- `NEWCLAW_REDMINE_MCP_TOKEN=...`
- `NEWCLAW_REDMINE_MCP_VERIFY_TLS=true`
- `NEWCLAW_STAGE8_SANDBOX_ASSIGNEE=ops_oncall`
- `NEWCLAW_STAGE8_SANDBOX_TRANSITION=In Progress`
- `NEWCLAW_STAGE8_LIVE_REQUESTED_BY=stage8_live_runner`
- `NEWCLAW_DB_PATH=/tmp/nestclaw-stage8-live.db`

## 실행 순서
1. feature worktree에서 변경을 커밋하고 QA worktree를 fast-forward 한다.
2. QA worktree에 runtime dependency(`fastapi`, `httpx`)가 있는지 확인한다.
3. sandbox env를 export 한다.
4. QA worktree에서 `bash scripts/run_stage8_live_rehearsal.sh`를 실행한다.
5. 리포트 `reports/qa/stage8-live-rehearsal-*.md`와 incident report path를 증적으로 보관한다.

## 기대 결과
- incident run은 `run_mode: mcp-live`로 `DONE`에 도달한다.
- 보고서에 `context_dry_run: True`, `mcp_dry_run: False`가 기록된다.
- sandbox ticket에 update/comment/assign/transition 이력이 남는다.
- 리포트 상태가 `PASS`로 종료된다.

## 실패 해석
- `SKIP`:
  - live enable flag 미설정
  - runtime dependency 미설치
  - MCP endpoint 또는 sandbox metadata 미설정
- `FAIL`:
  - MCP endpoint 응답 오류
  - incident run이 `DONE`에 도달하지 못함
  - lifecycle 후속 호출 중 하나라도 실패

## 롤백 / 정리
- sandbox issue를 `Closed` 또는 합의된 종료 상태로 전환한다.
- rehearsal comment에 테스트 종료 시각과 담당자를 남긴다.
- 실패 시 `reports/qa/stage8-live-rehearsal-*.md`를 기준으로 endpoint payload/response를 분석한다.

## 증적 위치
- live rehearsal report: `reports/qa/stage8-live-rehearsal-*.md`
- incident orchestration report: `reports/<incident_task_id>/incident_report.md`
- MWU 평가 노트: `work/micro_units/stage8-w5-001/EVALUATE_NOTES.md`
