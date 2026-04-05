# Stage 8 External Env Handoff Profile

## 목적
- Stage 8 sandbox/live readiness를 다시 열 때 필요한 external env contract를 한 문서로 고정한다.
- 운영자, 상위 에이전트, QA 실행자가 `왜 BLOCKED인지`, `누가 값을 줘야 하는지`, `어떻게 재확인할지`를 같은 vocabulary로 읽게 만든다.

## Canonical Blocker Baseline
- 최신 rerun summary: `STAGE8_QA_RERUN_STATUS_2026-04-05.md`
- 최신 readiness bundle: `/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/stage8-readiness-bundle-20260405T034720Z.md`
- 현재 canonical state: `BLOCKED`
- 핵심 이유: required external env 5개 미설정

## Required External Env
| Env | Scope | Owner | Secret | Example Format | Validation Rule |
| --- | --- | --- | --- | --- | --- |
| `NEWCLAW_STAGE8_SANDBOX_ENABLED` | sandbox rehearsal gate | sandbox operator | no | `1` | truthy 값이어야 한다 (`1/true/yes/on`) |
| `NEWCLAW_STAGE8_SANDBOX_BASE_URL` | sandbox target metadata | Redmine sandbox owner | no | `https://redmine-sandbox.example.internal` | `http://` 또는 `https://` URL |
| `NEWCLAW_STAGE8_SANDBOX_PROJECT` | sandbox target metadata | sandbox project owner | no | `OPS-SANDBOX` | 비어 있지 않은 project key |
| `NEWCLAW_STAGE8_LIVE_ENABLED` | live rehearsal gate | pilot release approver | no | `1` | truthy 값이어야 한다 (`1/true/yes/on`) |
| `NEWCLAW_REDMINE_MCP_ENDPOINT` | live MCP bridge | integration owner | no | `https://redmine-mcp.example.internal/api` | `http://` 또는 `https://` URL |

## Recommended External Env
| Env | Scope | Owner | Secret | Example Format | Notes |
| --- | --- | --- | --- | --- | --- |
| `NEWCLAW_REDMINE_MCP_TOKEN` | live MCP authentication | integration owner | yes | empty in repo, injected at runtime | repo에 기록하지 않는다 |
| `NEWCLAW_REDMINE_MCP_VERIFY_TLS` | live MCP TLS policy | integration owner | no | `true` | 미지정 시 runtime default를 따르지만 handoff 시 명시 권장 |
| `NEWCLAW_STAGE8_SANDBOX_ASSIGNEE` | live rehearsal lifecycle | sandbox process owner | no | `ops_oncall` | live rehearsal evidence에 같이 남는다 |
| `NEWCLAW_STAGE8_SANDBOX_TRANSITION` | live rehearsal lifecycle | sandbox process owner | no | `In Progress` | agreed workflow transition 명칭 |
| `NEWCLAW_STAGE8_LIVE_REQUESTED_BY` | audit hint | pilot operator | no | `stage8_live_runner` | optional operator trace field |

## Handoff Artifact
- canonical template: `configs/stage8_external_env.handoff.env.example`
- local validator: `scripts/validate_stage8_env_handoff.sh`
- resume runbook: `STAGE8_BLOCKED_TO_RESUMED_RUNBOOK_2026-04-05.md`

## Validation Workflow
1. template를 복사해 secure channel 또는 secret store 기준으로 값을 채운다.
2. repo에는 secret 값을 커밋하지 않는다.
3. 아래 validator로 required env completeness를 먼저 확인한다.
4. validator가 `READY`면 QA worktree에서 readiness bundle을 재실행한다.

```bash
cp configs/stage8_external_env.handoff.env.example /tmp/stage8_external_env.env
bash scripts/validate_stage8_env_handoff.sh /tmp/stage8_external_env.env
```

## QA Resume Command
```bash
cd /Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa
source .venv/bin/activate
set -a
source /tmp/stage8_external_env.env
set +a
bash scripts/run_stage8_readiness_bundle.sh
```

## Decision Mapping
- validator `READY` + readiness bundle `PASS`: live pilot evidence refresh 가능
- validator `READY` + readiness bundle `FAIL`: env completeness는 맞고 runtime/integration drill-down 필요
- validator `BLOCKED`: external env handoff incomplete, 코드 failure로 분류하지 않음

## Guardrails
- secret/token은 markdown, git history, QA report 본문에 남기지 않는다.
- enable flag가 `0` 또는 비어 있으면 configured로 보지 않는다.
- placeholder 예시를 실제 값처럼 운영자에게 전달하지 않는다.
