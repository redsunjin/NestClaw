# NestClaw Deployment Bootstrap Profiles

## 목적
- local dev, operator sidecar, upper-agent host가 같은 baseline으로 NestClaw HTTP API와 MCP stdio surface를 반복 가능하게 띄우도록 bootstrap profile을 고정한다.
- 이 문서는 사람이 읽는 guide이고, canonical machine-readable artifact는 `configs/deployment_bootstrap_profiles.json`이다.

## Canonical Artifacts
- profile source: `configs/deployment_bootstrap_profiles.json`
- validator: `bash scripts/validate_deployment_bootstrap_profiles.sh`
- transport baseline guide: `NESTCLAW_MCP_TRANSPORT_DEPLOYMENT_GUIDE.md`

## Common Baseline
- HTTP API baseline: `uvicorn app.main:APP`
- MCP baseline: `python3 app/mcp_server.py`
- canonical health endpoint: `GET /health`
- MCP readiness sequence: `initialize -> notifications/initialized -> tools/list -> catalog.manifest`

## Profile Summary
| Profile | Primary Use | HTTP | MCP | Recommended Auth |
| --- | --- | --- | --- | --- |
| `local_dev` | workstation 개발/디버그 | required, `--reload` | required | `jwt_local` |
| `operator_sidecar` | 내부 운영자/sidecar 배치 | required, no reload | required | `trusted_sso_headers` or `jwt_idp` |
| `upper_agent_host` | 상위 에이전트 host | optional for UI/health | required, stdio child | `jwt_local` or trusted actor injection |

## Local Dev
- 목적: 브라우저 UI, CLI, MCP를 한 머신에서 동시에 확인
- HTTP:
```bash
uvicorn app.main:APP --host 127.0.0.1 --port 8000 --reload
```
- MCP:
```bash
python3 app/mcp_server.py
```
- 권장 auth:
  - local JWT
  - default actor role: `requester`
- readiness:
  1. `curl http://127.0.0.1:8000/health`
  2. MCP initialize
  3. `catalog.manifest`

## Operator Sidecar
- 목적: human operator dashboard와 내부 sidecar automation을 같은 trust boundary에서 운영
- HTTP:
```bash
uvicorn app.main:APP --host 127.0.0.1 --port 8000
```
- MCP:
```bash
python3 app/mcp_server.py
```
- 권장 auth:
  - `trusted_sso_headers` 또는 `jwt_idp`
  - default actor role: `reviewer`
  - `approver/admin`은 명시적 human boundary에서만 사용
- 운영 메모:
  - HTTP와 MCP를 supervisor 아래 별도 프로세스로 관리
  - 비정상 종료 시 프로세스 단위 재기동

## Upper-Agent Host
- 목적: Claude/Codex/internal chat agent host가 NestClaw orchestration을 child process로 사용
- HTTP:
```bash
uvicorn app.main:APP --host 127.0.0.1 --port 8000
```
- MCP:
```bash
python3 app/mcp_server.py
```
- 권장 auth:
  - requester/reviewer default
  - actor context는 host가 명시적으로 주입
- 운영 메모:
  - primary surface는 MCP stdio child process
  - HTTP는 dashboard, health, fallback integration 확인용 optional sidecar
  - remote gateway는 아직 baseline이 아니다

## Restart / Health Rules
- HTTP health: `/health == {"status":"ok"}`
- MCP ready: `tools/list`와 `catalog.manifest`가 성공해야 ready로 본다
- restart trigger:
  - local dev: 코드 변경 시 HTTP reload, MCP는 수동 재시작
  - operator sidecar: 프로세스 종료/health failure 시 supervisor 재시작
  - upper-agent host: child process EOF/non-zero exit 시 host가 재spawn

## Preflight
```bash
bash scripts/validate_deployment_bootstrap_profiles.sh
```

## Guardrails
- bootstrap profile은 remote MCP exposure를 productized feature처럼 설명하지 않는다.
- actor context 기본값은 low-privilege role을 유지한다.
- secret/token 값은 profile artifact에 넣지 않는다.
