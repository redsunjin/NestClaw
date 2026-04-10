# NestClaw MCP Transport Deployment Guide

## 1. 목적
- 이 문서는 상위 에이전트나 MCP client가 NestClaw MCP를 반복적으로 붙일 때 필요한 startup, transport, auth boundary를 고정한다.
- 목표는 "지금 실제로 지원되는 경계"를 분명히 하는 것이다.
- profile별 bootstrap 묶음은 `NESTCLAW_DEPLOYMENT_BOOTSTRAP_PROFILES_2026-04-08.md`와 `configs/deployment_bootstrap_profiles.json`를 기준으로 본다.

## 2. 현재 지원 범위
- 현재 productized baseline은 `stdio MCP server`다.
- 실행 명령은 아래 한 가지를 기준으로 본다.

```bash
python3 app/mcp_server.py
```

- 상위 agent 또는 MCP host는 이 프로세스를 child process로 띄우고 stdio로 JSON-RPC 메시지를 주고받는다.
- 현재 repo는 별도의 remote HTTP/SSE/WebSocket MCP gateway를 packaged feature로 제공하지 않는다.

## 3. 권장 연결 순서
1. MCP child process spawn
2. `initialize`
3. `notifications/initialized`
4. `tools/list`
5. `catalog.manifest`
6. `agent.submit/status/events/recent/report/bundle` observe loop

권장 이유:
- `catalog.manifest`를 먼저 읽으면 readiness, safe control, role boundary를 연결 시작 전에 파악할 수 있다.
- `agent.bundle`까지 포함한 observe loop를 표준으로 보면 상위 agent가 상태를 추정하지 않고 runtime facts를 읽게 된다.

## 4. Actor / Auth Boundary
- 모든 MCP tool call은 `actor_id`를 포함해야 한다.
- `actor_role`도 명시하는 편이 좋다. 일부 tool은 default role이 있지만, upper-agent integration에서는 implicit role에 기대지 않는 편이 안전하다.
- 안전한 기본값은 `requester` 또는 `reviewer`다.
- `approver` / `admin`은 명시적 인간 승인 또는 운영 위임이 있을 때만 사용한다.

예:

```json
{
  "task_id": "task_xxxxx",
  "actor_id": "claude_user",
  "actor_role": "requester"
}
```

## 5. Safe vs Elevated Control
### 5.1 기본적으로 안전한 observe/control
- `agent.submit`
- `agent.status`
- `agent.events`
- `agent.recent`
- `agent.report`
- `agent.bundle`
- `catalog.manifest`
- `catalog.list`
- `catalog.get`
- `catalog.create_draft`
- `catalog.get_draft`
- `catalog.validate_draft`

### 5.2 elevated control
- `approval.approve`
- `approval.reject`
- `catalog.apply_draft`
- `catalog.rollback_tool`

원칙:
- elevated control은 approver/admin trust boundary 안에서만 사용한다.
- 상위 agent가 기본 requester identity로 붙는 경우, elevated tool을 기본 flow에 넣지 않는다.

## 6. Transport / Deployment Guidance
### 6.1 지금 권장하는 배치
- 로컬 개발: upper-agent host가 `python3 app/mcp_server.py`를 child process로 실행
- 내부 배치/agent worker: 동일 trust boundary 안 sidecar process로 실행

### 6.2 아직 productized 하지 않은 것
- remote SSE gateway
- public network exposure
- dedicated auth termination proxy
- tenant-aware MCP gateway

이 항목들은 future hardening boundary이지, 현재 지원 계약이 아니다.

### 6.3 운영 시 주의점
- stdio MCP는 한 trust boundary당 한 프로세스로 단순하게 두는 편이 낫다.
- process 장애 시 재기동 가능하게 만드는 것이 중요하다.
- readiness 확인은 `initialize -> tools/list -> catalog.manifest` 세 단계면 충분하다.
- network-exposed deployment가 필요하면, 별도 wrapper가 auth를 종료하고 actor context를 주입하는 구조를 먼저 설계해야 한다.

## 7. Smoke / Verification
- 기본 smoke:
  - `python3 -m unittest tests.test_mcp_server_smoke`
  - `python3 -m unittest tests.test_stage10_contract`
- 전체 cycle:
  - `bash scripts/run_dev_qa_cycle.sh 10`

## 8. 한 줄 요약
- 현재 NestClaw MCP는 `stdio baseline`이 canonical transport이고, remote deployment는 아직 문서상 future boundary다.
