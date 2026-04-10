# Stage 8 External Env Request Kit

## 목적
- 외부 운영 담당자에게 Stage 8 readiness unblock 요청을 바로 전달할 수 있도록 복붙 가능한 메시지와 체크리스트를 제공한다.
- 요청자가 `왜 필요한지`, `무엇이 비어 있는지`, `어떤 형식으로 받으면 되는지`를 한 번에 전달하게 만든다.

## Current Snapshot
- 최신 readiness bundle: `/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/stage8-readiness-bundle-20260410T131205Z.md`
- 최신 self-eval: `/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa/reports/qa/stage8-self-eval-20260410T131205Z.md`
- 현재 canonical state: `BLOCKED`
- 핵심 이유: external env 5개 미설정

## Copy/Paste Request Message
```text
안녕하세요.

NestClaw Stage 8 sandbox/live readiness를 다시 실행하려면 아래 external env/metadata가 필요합니다.
현재 최신 readiness 결과는 BLOCKED이며, 코드 이슈가 아니라 운영 입력 부족 상태입니다.

필수 값:
- NEWCLAW_STAGE8_SANDBOX_ENABLED=1
- NEWCLAW_STAGE8_SANDBOX_BASE_URL=<sandbox base url>
- NEWCLAW_STAGE8_SANDBOX_PROJECT=<sandbox project key>
- NEWCLAW_STAGE8_LIVE_ENABLED=1
- NEWCLAW_REDMINE_MCP_ENDPOINT=<live mcp endpoint>

권장 추가 값:
- NEWCLAW_REDMINE_MCP_TOKEN=<secure channel only>
- NEWCLAW_REDMINE_MCP_VERIFY_TLS=true|false
- NEWCLAW_STAGE8_SANDBOX_ASSIGNEE=<assignee>
- NEWCLAW_STAGE8_SANDBOX_TRANSITION=<transition name>
- NEWCLAW_STAGE8_LIVE_REQUESTED_BY=<operator id>

중요:
- token/secret 값은 이 스레드나 문서에 적지 말고 별도 secure channel로 전달해주세요.
- 응답은 가능하면 아래 env 형식 그대로 보내주시면 됩니다.

응답 형식 예시:
NEWCLAW_STAGE8_SANDBOX_ENABLED=1
NEWCLAW_STAGE8_SANDBOX_BASE_URL=https://redmine-sandbox.example.internal
NEWCLAW_STAGE8_SANDBOX_PROJECT=OPS-SANDBOX
NEWCLAW_STAGE8_LIVE_ENABLED=1
NEWCLAW_REDMINE_MCP_ENDPOINT=https://redmine-mcp.example.internal/api
NEWCLAW_REDMINE_MCP_VERIFY_TLS=true
NEWCLAW_STAGE8_SANDBOX_ASSIGNEE=ops_oncall
NEWCLAW_STAGE8_SANDBOX_TRANSITION="In Progress"
NEWCLAW_STAGE8_LIVE_REQUESTED_BY=stage8_live_runner

값을 받는 즉시 validator와 readiness bundle을 다시 실행해서 PASS/FAIL/BLOCKED를 다시 공유하겠습니다.
```

## Sender Checklist
- 최신 blocked 증적 경로를 함께 전달했는가
- 필수 5개 env와 권장 추가값을 구분해서 적었는가
- token/secret은 secure channel로 따로 달라고 명시했는가
- sandbox owner / integration owner / release approver 중 누구에게 요청하는지 분명한가
- 응답 형식을 env line 기준으로 요청했는가

## Receiver Checklist
- `NEWCLAW_STAGE8_SANDBOX_ENABLED`가 truthy 값인가
- `NEWCLAW_STAGE8_SANDBOX_BASE_URL`이 URL 형식인가
- `NEWCLAW_STAGE8_SANDBOX_PROJECT`가 비어 있지 않은가
- `NEWCLAW_STAGE8_LIVE_ENABLED`가 truthy 값인가
- `NEWCLAW_REDMINE_MCP_ENDPOINT`가 URL 형식인가
- token이 있다면 secure channel로만 전달됐는가

## Local Validation
```bash
cp configs/stage8_external_env.handoff.env.example /tmp/stage8_external_env.env
# 받은 값으로 /tmp/stage8_external_env.env 채우기
bash scripts/validate_stage8_env_handoff.sh /tmp/stage8_external_env.env
```

## QA Re-Run
```bash
cd /Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa
source .venv/bin/activate
set -a
source /tmp/stage8_external_env.env
set +a
bash scripts/run_stage8_readiness_bundle.sh
```

## Expected Outputs
- `reports/qa/stage8-readiness-bundle-*.md`
- `reports/qa/stage8-self-eval-*.md`
- `reports/qa/stage8-sandbox-e2e-*.md`
- `reports/qa/stage8-live-rehearsal-*.md`
