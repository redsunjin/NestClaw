# NestClaw Integration Examples

## 1. 목적
- 이 문서는 상위 대화형 에이전트, MCP client, CLI wrapper, HTTP caller가 NestClaw를 어떻게 호출해야 하는지 concrete example로 보여준다.

## 2. Claude-style Upper Agent Operating Pattern
상위 에이전트에게 권장하는 최소 운영 규칙:

1. 사용자의 목표를 요약해서 NestClaw에 넘긴다.
2. 완료 여부를 추정하지 말고 반드시 status/report를 확인한다.
3. approval이 필요하면 사람에게 handoff한다.
4. tool selection은 직접 흉내 내지 말고 NestClaw planner를 신뢰한다.

권장 시스템 지침 예시:

```text
You use NestClaw as an orchestration backend.
Always submit work through NestClaw, observe status/events, and read the final report before answering.
Do not self-approve high-risk actions unless an explicit human-approved approver role is provided.
Treat NEEDS_HUMAN_APPROVAL and BLOCKED as unfinished states.
```

## 3. MCP Example
### 3.0 stdio Bootstrap

```bash
python3 app/mcp_server.py
```

운영 전제:
- 현재 canonical MCP transport는 stdio다.
- upper-agent host가 child process로 붙는 구성을 기본으로 본다.
- remote gateway/SSE 배포는 아직 future boundary다.
- 가능한 모든 tool call에 `actor_id`, `actor_role`를 명시한다.

### 3.1 Read Manifest First
Tool: `catalog.manifest`

```json
{
  "actor_id": "claude_user",
  "actor_role": "requester"
}
```

### 3.2 Submit
Tool: `agent.submit`

```json
{
  "request_text": "주간 운영회의 메모를 요약하고 액션 아이템을 정리해줘",
  "requested_by": "claude_user",
  "task_kind": "auto",
  "title": "주간 운영회의 요약",
  "metadata": {
    "meeting_title": "주간 운영회의",
    "meeting_date": "2026-04-04",
    "participants": ["Kim", "Lee"],
    "notes": "업무A 진행\n업무B 리스크\n업무C 일정"
  },
  "auto_run": true,
  "actor_id": "claude_user",
  "actor_role": "requester"
}
```

### 3.3 Poll Status
Tool: `agent.status`

```json
{
  "task_id": "task_xxxxx",
  "actor_id": "claude_user",
  "actor_role": "requester"
}
```

해석:
- `RUNNING`: 계속 polling
- `NEEDS_HUMAN_APPROVAL`: 사람에게 handoff
- `DONE`: report 읽기

### 3.4 Fetch Events
Tool: `agent.events`

```json
{
  "task_id": "task_xxxxx",
  "actor_id": "claude_user",
  "actor_role": "requester"
}
```

### 3.5 Recent / Report
Tool: `agent.recent`

```json
{
  "actor_id": "claude_user",
  "actor_role": "requester",
  "limit": 5
}
```

Tool: `agent.report`

```json
{
  "task_id": "task_xxxxx",
  "actor_id": "claude_user",
  "actor_role": "requester",
  "max_chars": 1500
}
```

### 3.6 Approval Handoff
사람 approver가 있을 때만:

Tool: `approval.list`

```json
{
  "status": "PENDING",
  "actor_id": "qa_approver",
  "actor_role": "approver"
}
```

Tool: `approval.get`

```json
{
  "queue_id": "aq_xxxxx",
  "actor_id": "qa_approver",
  "actor_role": "approver"
}
```

Tool: `approval.approve`

```json
{
  "queue_id": "aq_xxxxx",
  "acted_by": "qa_approver",
  "comment": "approved after human review",
  "actor_id": "qa_approver",
  "actor_role": "approver"
}
```

주의:
- `approval.approve`, `approval.reject`, `catalog.apply_draft`, `catalog.rollback_tool`은 기본 requester flow에 넣지 않는다.
- upper-agent가 elevated control을 쓸 때는 명시적 approver/admin trust boundary가 있어야 한다.

## 4. HTTP Example
### 4.0 Capabilities
```bash
curl http://127.0.0.1:8000/api/v1/capabilities \
  -H 'X-Actor-Id: qa_user' \
  -H 'X-Actor-Role: requester'
```

### 4.1 Submit
```bash
curl -X POST http://127.0.0.1:8000/api/v1/agent/submit \
  -H 'Content-Type: application/json' \
  -H 'X-Actor-Id: qa_user' \
  -H 'X-Actor-Role: requester' \
  -d '{
    "task_kind": "auto",
    "title": "주간 운영회의 요약",
    "request_text": "주간 운영회의 메모를 요약하고 액션 아이템을 정리해줘",
    "requested_by": "qa_user",
    "metadata": {
      "meeting_title": "주간 운영회의",
      "meeting_date": "2026-04-04",
      "participants": ["Kim", "Lee"],
      "notes": "업무A 진행\n업무B 리스크\n업무C 일정"
    },
    "auto_run": true,
    "incident_run_mode": "dry-run"
  }'
```

### 4.2 Status
```bash
curl http://127.0.0.1:8000/api/v1/agent/status/task_xxxxx \
  -H 'X-Actor-Id: qa_user' \
  -H 'X-Actor-Role: requester'
```

### 4.3 Events
```bash
curl http://127.0.0.1:8000/api/v1/agent/events/task_xxxxx \
  -H 'X-Actor-Id: qa_user' \
  -H 'X-Actor-Role: requester'
```

### 4.4 Report Preview
```bash
curl "http://127.0.0.1:8000/api/v1/agent/report/task_xxxxx?max_chars=4000" \
  -H 'X-Actor-Id: qa_user' \
  -H 'X-Actor-Role: requester'
```

### 4.5 Recent / Approval Detail
```bash
curl "http://127.0.0.1:8000/api/v1/agent/recent?limit=5" \
  -H 'X-Actor-Id: qa_user' \
  -H 'X-Actor-Role: requester'

curl "http://127.0.0.1:8000/api/v1/approvals/aq_xxxxx" \
  -H 'X-Actor-Id: qa_approver' \
  -H 'X-Actor-Role: approver'
```

## 5. CLI Example
### 5.0 Capabilities
```bash
python3 app/cli.py capabilities --actor-id qa_user --actor-role requester --json
```

### 5.1 Submit
```bash
python3 app/cli.py submit \
  --request-text "주간 운영회의 메모를 요약하고 액션 아이템을 정리해줘" \
  --requested-by qa_user \
  --task-kind auto \
  --title "주간 운영회의 요약" \
  --metadata-json '{"meeting_title":"주간 운영회의","meeting_date":"2026-04-04","participants":["Kim","Lee"],"notes":"업무A 진행\n업무B 리스크\n업무C 일정"}' \
  --actor-id qa_user \
  --actor-role requester \
  --json
```

### 5.2 Status / Events
```bash
python3 app/cli.py status --task-id task_xxxxx --actor-id qa_user --actor-role requester --json
python3 app/cli.py events --task-id task_xxxxx --actor-id qa_user --actor-role requester --json
```

### 5.3 Recent / Report / Approval Detail
```bash
python3 app/cli.py recent --actor-id qa_user --actor-role requester --json
python3 app/cli.py report --task-id task_xxxxx --actor-id qa_user --actor-role requester --json
python3 app/cli.py handoff --task-id task_xxxxx --actor-id qa_user --actor-role requester --json
python3 app/cli.py approvals --actor-id qa_approver --actor-role approver --json
python3 app/cli.py approval-get --queue-id aq_xxxxx --actor-id qa_approver --actor-role approver --json
```

### 5.4 Approval
```bash
python3 app/cli.py approve \
  --queue-id aq_xxxxx \
  --acted-by qa_approver \
  --actor-id qa_approver \
  --actor-role approver \
  --comment "approved after review" \
  --json
```

## 6. Tool Governance Example
### 6.1 Draft
```bash
python3 app/cli.py tool-draft \
  --requested-by qa_user \
  --request-text "Slack 알림 도구를 추가하고 싶다" \
  --actor-id qa_user \
  --actor-role requester \
  --json
```

### 6.2 Validate
```bash
python3 app/cli.py tool-validate \
  --draft-id tooldraft_xxxxx \
  --actor-id qa_user \
  --actor-role reviewer \
  --json
```

### 6.3 Apply
```bash
python3 app/cli.py tool-apply \
  --draft-id tooldraft_xxxxx \
  --acted-by qa_approver \
  --actor-id qa_approver \
  --actor-role approver \
  --json
```

## 7. Upper Agent Completion Checklist
- `submit` 응답에서 `task_id`를 저장했는가
- `status`로 `DONE` 또는 `NEEDS_HUMAN_APPROVAL`을 확인했는가
- `events`에서 planner provenance를 확인했는가
- approval pending이면 사람에게 명확히 넘겼는가
- 최종 응답 전에 report preview/raw를 읽었는가

## 8. Recommended Next Example
- 이후에는 이 문서를 기반으로 실제 MCP transcript fixture 또는 smoke scenario를 추가하는 것이 좋다.
