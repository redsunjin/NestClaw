[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# 로컬 업무 위임 오케스트레이션 (기본문서)

## 문서 목적
이 문서는 전문가 그룹 검토를 바탕으로 프로젝트의 목적, 개발 계획, 현실적 접근 방안을 정의하는 기본 기준 문서다.

상세 검토 원문은 `REVIEW_REPORT.md`를 따른다.

## 1) 프로젝트 목적
### 1.1 핵심 목적
- 로컬 환경에서 안전하게 동작하는 **정책·승인·감사를 갖춘 orchestration AI agent**를 구현한다.
- 이 에이전트는 하나의 요청을 받아 다양한 도구를 계획적으로 사용하고, 필요한 승인과 감사로그를 남기면서 실제 업무 처리까지 이어지는 것을 목표로 한다.
- 사용자는 목표를 주고, 시스템은 AI를 기본 실행 경로로 사용해 계획/도구선택/실행/검토/보고를 수행한다.
- heuristic/template 경로는 주 경로가 아니라 운영 연속성을 위한 `degraded mode`로만 유지한다.

### 1.2 운영 원칙
- 감시형이 아닌 업무 위임형
- 최소 권한/최소 수집
- 정책 기반 실행
- 승인 가능한 자동화
- 감사 가능한 로그

### 1.3 제외 범위
- 사적 영역 기본 접근(개인 파일/메신저/사진 등)
- 정책 우회 자동 실행
- 설명 불가능한 블랙박스 실행

## 2) 전문가 그룹 검토 요약
기준 문서: `AGENT_EXPERT_GROUP.md`  
검토보고서: `REVIEW_REPORT.md`
최신 업데이트: `EXPERT_REVIEW_UPDATE_2026-02-24.md`

- 종합 판정: **조건부 진행 가능 (Go with Guardrails)**
- 최신 판정(2026-02-24): **유효함 (조건부 High)**
- 핵심 조건:
  - 목적과 범위를 업무 위임으로 고정
  - 정책 엔진/승인 게이트를 초기부터 포함
  - `create/run/status` 중심 단일 흐름 우선 구현
  - 기능 확장보다 안정성/재현성 우선

## 3) 현실적인 접근 방안 (Step 기반)
### Step 1. 목적/성공기준 고정
- 목표: 업무 위임 1개 흐름 end-to-end 자동화
- 성공기준:
  - 작업 생성/실행/상태 조회 동작
  - 실패 시 재시도 1회
  - 위험 액션 차단
  - 로그 기반 추적 가능

### Step 2. 최소 구조 구현
- 구성: `api`, `orchestrator`, `agents`, `policy`, `logs`
- 최소 엔드포인트: `/task/create`, `/task/run`, `/task/status`

### Step 3. 단일 에이전트 체인 고정
- 실행 체인: `planner -> executor -> reviewer -> reporter`
- 목표: 단일 입력에서 결과 리포트까지 재현 가능하게 실행

### Step 4. 정책/권한 선적용
- 허용 경로 화이트리스트
- 위험 명령 차단(`rm`, 외부 전송 등)
- 차단 사유 및 실행 주체를 로그에 기록

### Step 5. 실패 복구/승인 전환
- 상태 코드:
  - `READY`, `RUNNING`, `FAILED_RETRYABLE`, `NEEDS_HUMAN_APPROVAL`, `DONE`
- 규칙:
  - 재시도 1회 후 실패 시 사람 승인 대기

### Step 6. 검증 및 확장 결정
- 테스트 축: 정상/실패/차단
- 확장 조건:
  - 정책 위반 0
  - 로그 누락 0
  - 회귀 테스트 통과

## 4) 개발 계획 (실행 단위)
1. 기본 API + 상태머신 스켈레톤 구현
2. planner/executor/reviewer 체인 연결
3. 정책 엔진 + 차단 룰 적용
4. 재시도/승인 전환 로직 적용
5. 검토 리포트 출력 포맷 고정
6. 회귀 시나리오로 품질 게이트 운영

## 5) 의사결정 및 책임
- 목표/범위: Product Owner Agent (A01)
- 구현/오케스트레이션: Workflow Engineer (A02), LLM Orchestrator (A03)
- 정책/보안: Security Privacy (A04)
- 운영 UX: UX Operations (A05)
- 테스트 게이트: QA Reliability (A06)
- 자문: Compliance (A07), Domain SME (A08)

## 6) 산출물 기준
- 필수 산출물:
  - 실행 로그
  - 검토 리포트
  - 상태 조회 결과
  - 차단/승인 이력
- 품질 체크:
  - 성공 기준 충족
  - 정책 위반 없음
  - 로그 누락 없음
  - 실패 복구 동작 확인

## 7) 즉시 시작 항목
1. `create/run/status` API 계약 고정
2. 상태 코드와 전이 규칙 문서화
3. 화이트리스트 경로/도구 정책 정의
4. 첫 번째 표준 검증 시나리오 3종(정상/실패/차단) 작성

## 8) 비IT/기업 적용성 검증 결과
상세 보고서: `FEASIBILITY_VALIDATION_REPORT.md`

- 비IT 업무자: 조건부 가능 (템플릿 UX + 안전 기본값 + 실패 안내가 전제)
- 회사 적용: 실행 가능 (RBAC + 감사 로그 + 정책 팩 운영이 전제)
- 공통 성공요인:
  - 업무 템플릿화
  - 승인/권한/정책 내장
  - 회귀 게이트 통과 후 확장

## 9) 실행 문서
- 실행 체크리스트: `TASKS.md`
- 아이디에이션 1페이지(역할 경계/의사결정 기준): `IDEATION_ONEPAGER.md`
- 비IT 업무 템플릿 3종: `NON_IT_WORK_TEMPLATES.md`
- API 계약서 초안: `API_CONTRACT.md`
- 상태 전이 문서: `STATE_MACHINE.md`
- 정책 화이트리스트 초안: `POLICY_WHITELIST.md`
- 승인 큐 데이터 모델: `APPROVAL_QUEUE_MODEL.md`
- 회의요약 템플릿 테스트 계획: `TEMPLATE_MEETING_SUMMARY_TEST_PLAN.md`
- Stage 8 실행안(운영장애 + RAG/MCP): `INCIDENT_ORCHESTRATION_RAG_MCP_PLAN.md`
- Stage 8 실행 체크리스트: `STAGE8_EXECUTION_CHECKLIST_2026-03-04.md`
- Stage 8 상세 설계: `STAGE8_DETAILED_DESIGN_2026-03-04.md`
- Stage 8 자체평가 그룹: `STAGE8_SELF_EVAL_GROUPS_2026-03-05.md`
- Stage 8 종료 요약: `STAGE8_CLOSEOUT_SUMMARY_2026-03-06.md`
- Stage 8 live rehearsal runbook: `STAGE8_LIVE_REHEARSAL_RUNBOOK_2026-03-07.md`
- Agent tool surface 방향: `AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md`
- Stage 8 마이크로 작업 프로토콜: `MICRO_AGENT_WORKFLOW.md`

## 10) 현재 구현 상태
- API 스켈레톤 구현 완료:
  - `POST /api/v1/agent/submit`
  - `GET /api/v1/agent/status/{task_id}`
  - `GET /api/v1/agent/events/{task_id}`
  - `POST /api/v1/task/create`
  - `POST /api/v1/task/run`
  - `GET /api/v1/task/status/{task_id}`
  - `GET /api/v1/task/events/{task_id}`
  - `GET /api/v1/approvals`
  - `POST /api/v1/approvals/{queue_id}/approve`
  - `POST /api/v1/approvals/{queue_id}/reject`
  - `GET /api/v1/audit/summary`
- 오케스트레이션 체인 구현: `planner -> executor -> reviewer -> reporter`
- 재시도/승인 전환 구현: 재시도 1회 후 승인 큐 전환
- 회의요약 템플릿 보고서 생성 구현: `reports/<task_id>/report.md`
- 인증/권한:
  - 로컬 JWT(`Authorization: Bearer <token>`)
  - 외부 IdP 토큰(`X-SSO-Token`) + JWKS 서명 검증
  - 선택형 SSO 헤더(`X-SSO-User`, `X-SSO-Role`, `NEWCLAW_ALLOW_TRUSTED_SSO_HEADERS=1`)
  - 호환 헤더(`X-Actor-Id`, `X-Actor-Role`, `NEWCLAW_ALLOW_COMPAT_HEADERS=1`)
- 영속 저장소:
  - SQLite 기본값 (`NEWCLAW_DB_BACKEND=sqlite`, `NEWCLAW_DB_PATH=data/new_claw.db`)
  - PostgreSQL 지원 (`NEWCLAW_DB_BACKEND=postgres`, `NEWCLAW_DATABASE_URL=...`)
- Stage 8 어댑터 스켈레톤:
  - Incident RAG 어댑터 계약 구현 (`app/incident_rag.py`)
  - Redmine MCP 어댑터 계약 구현 (`app/incident_mcp.py`)
  - 마이크로 유닛 게이트 운영 (`work/micro_units/stage8-w2-001/`)
- 현재 사용자 진입점:
  - 기본 진입점은 `agent submit/status/events`
  - `task/*`, `incident/*`는 하위 호환 및 세부 검증용
- 현재 내부 구조:
  - FastAPI route는 얇은 adapter로 유지
  - agent/task/incident orchestration은 `app/services/orchestration_service.py`로 분리

### 10.1 지금 실제로 할 수 있는 것
- 하나의 agent 요청을 받아 현재 구현된 workflow family(`task`, `incident`) 중 하나로 분기
- `task_kind=auto` 요청을 LLM intent classifier + heuristic fallback으로 안전하게 분류
- 회의요약 입력을 받아 액션 아이템 보고서 생성
- incident 입력을 받아 context 집계, action card, 승인/실행, 보고서 흐름을 dry-run으로 재현
- 승인 큐/이벤트 로그/audit/상태 조회를 일관된 경로로 처리
- MCP server를 통해 외부 AI가 `agent.submit/status/events`, `approval.*`, `catalog.*`를 호출 가능
- Redmine MCP live bridge 및 rehearsal script를 통해 sandbox 연동 경로 준비
- `configs/model_registry.yaml`를 runtime에서 읽고 provider selection과 intent classification provenance를 status/event에 기록
- `meeting_summary` workflow는 provider selection 뒤 실제 provider invocation을 시도하고 실패 시 템플릿 renderer로 fallback
- `task` workflow는 LLM planner를 통해 `internal.summary.generate`, `redmine.issue.create`, `slack.message.send` 중 필요한 action plan을 만들고, `planning_provenance.eligible_tools`를 상태/이벤트에 기록
- local LM Studio(`http://localhost:1234`)를 intent classifier provider로 등록해 사용할 수 있음
- `slack.message.send` tool capability를 catalog에 등록했고 incident workflow에서 `notify_channel` 입력 시 함께 계획/실행할 수 있음
- `/api/v1/tool-drafts`, `tool-draft`, `catalog.create_draft/get_draft`를 통해 reviewable tool registration draft를 생성할 수 있음
- approver/admin은 draft를 `overlay registry`에 apply할 수 있고, apply 직후 catalog/runtime이 새 tool을 즉시 반영함
- 브라우저 root(`/`)는 단일 사용 Quickstart 화면이고, 고급 운영 화면은 `/console`에 제공함
- Web Console에서 agent 자연어 요청을 제출하고 status/events를 같은 화면에서 확인할 수 있음
- Web Console에서 승인 큐를 조회하고 approve/reject를 처리할 수 있음
- Web Console에서 최근 task / 최근 approval 히스토리를 볼 수 있음
- Web Console에서 최근 task와 현재 task의 report preview / raw report 열기를 할 수 있음
- Web Console에서 approval 상세와 comment/history를 drill-down 할 수 있음
- 전문가 에이전트 운영 프로토콜 문서와 wrapper script를 통해 `Plan -> Review -> Implement -> Evaluate -> Sync` 절차를 강제할 수 있음
- priority campaign 레이어를 통해 여러 우선순위 MWU를 `pending -> in_progress -> completed`로 끊김 없이 이어갈 수 있음

### 10.1.1 현재 제품 위치
- 현재 NestClaw는 `AI-first orchestration agent`로 가는 전환기 상태다.
- `task` workflow는 이제 LLM planner가 기본 경로고, 실패나 비활성 시에만 degraded mode fallback으로 내려간다.
- task planner 범위는 `summary + ticket + slack`까지 넓어졌지만, 여전히 tool set이 좁고 `incident` workflow는 deterministic/dry-run 중심이다.
- incident workflow도 이제 `planned_actions + planning_provenance` 관측 계약을 공유하지만, planner 자체는 아직 deterministic/dry-run 중심이다.
- 따라서 현재 런타임은 `task AI-first baseline + incident common contract` 단계이며, product 전체로 보면 아직 완성형 multi-tool orchestration agent는 아니다.

### 10.2 아직 못 하는 것
- broader registry 기반 multi-step planning 확장 (`task` beyond summary/ticket/slack, incident AI planner, richer cross-action binding)
- live RAG 기반 reasoning
- production-ready MCP host packaging / remote transport hardening
- 운영자용 전용 GUI 콘솔

### 10.3 다음 고도화 방향
- `코어 서비스 -> HTTP/CLI/MCP 공통 표면` 구조로 재구성
- menu형 CLI를 유지하되, 별도로 비대화형 tool CLI를 제공
- MCP server를 통해 외부 AI가 `agent.submit/status/events`, `approval.*`, `catalog.*`를 직접 호출 가능하게 확장
- `configs/tool_registry.yaml` 기반 execution tool catalog와 capability schema를 실제 실행 계층에 연결했다
- `model registry selection -> provider invocation`은 summary path에 연결했다
- `planned_actions -> execution_call -> adapter dispatch` 공통 루프를 task/incident에 적용했다
- 다음 1순위는 cross-action data binding과 richer sequencing을 넣어 multi-step plan의 실행 품질을 높이는 것이다
- tool registry apply는 source yaml이 아니라 `work/tool_registry_runtime.yaml` overlay에 반영한다
- incident workflow는 broader execution agent의 첫 번째 high-risk vertical이며, 이후 일반 업무/운영 작업/티켓 처리 흐름으로 확장한다
- 그 다음 단계는 action-card/tool planning 공통 루프와 최소 operator UI다
- 상세 방향 문서: `AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md`

### 10.4 상위 호출 계층
- NestClaw는 독립 UI로도 쓸 수 있지만, 상위 UX/상위 에이전트가 호출하는 하위 orchestration runtime이 될 수도 있다.
- 예: `rfs-cli -> NestClaw -> Slack/Redmine/...`
- 이 구조에서도 계획/도구 선택/승인 판단의 주체는 NestClaw이며, 상위 호출자는 고수준 목표만 넘긴다.

코드 위치:
- 서버: `app/main.py`
- 서비스 계층: `app/services/orchestration_service.py`
- 승인 서비스 계층: `app/services/approval_service.py`
- 도구 카탈로그 서비스 계층: `app/services/tool_catalog_service.py`
- 도구 draft 서비스 계층: `app/services/tool_draft_service.py`
- 도구 CLI: `app/cli.py`
- MCP server: `app/mcp_server.py`
- 모델 레지스트리: `app/model_registry.py`
- provider invoker: `app/provider_invoker.py`
- 도구 레지스트리: `app/tool_registry.py`
- Slack adapter: `app/slack_adapter.py`
- intent classifier: `app/intent_classifier.py`
- 의존성: `requirements.txt`

## 11) 로컬 실행 방법
1. 의존성 설치
```bash
python3 -m pip install -r requirements.txt
```

2. 서버 실행
```bash
uvicorn app.main:APP --reload --port 8000
```

2-1. 가장 쉬운 확인: Quickstart
```text
http://127.0.0.1:8000/
```
- 한 개의 자연어 요청 입력
- 현재 상태/보고서/승인 요약
- 최근 요청 다시 불러오기
- 승인 필요 시 approver/admin role로 바꿔 approve/reject

2-2. 고급 운영 화면: Web Console
```text
http://127.0.0.1:8000/console
```
- 도구 목록 조회
- agent 요청 제출
- status / events 조회
- 승인 큐 조회 / approve / reject
- 최근 task / 최근 approval 히스토리
- approval 상세 / comment history drill-down
- tool draft 생성
- draft 조회/적용
- 로컬 개발 모드에서는 `X-Actor-Id`, `X-Actor-Role` 헤더를 브라우저 UI가 직접 넣어 호출

다음 작업 그룹 계획:
- `NEXT_WORK_GROUPS_2026-03-13.md`

3. 로컬 tool CLI 실행
```bash
python3 app/cli.py submit --requested-by qa_user --task-kind task --request-text "운영회의 요약" --metadata-json '{"meeting_title":"ops sync","meeting_date":"2026-03-12","participants":["Kim"],"notes":"internal only"}' --json
python3 app/cli.py status --task-id <task_id> --actor-id qa_user --json
python3 app/cli.py events --task-id <task_id> --actor-id qa_user --json
```

4. interactive menu CLI 실행
```bash
python3 app/cli.py
```

5. MCP stdio server 실행
```bash
python3 app/mcp_server.py
```

6. LM Studio intent classifier 사용
```bash
export NEWCLAW_ENABLE_LLM_INTENT=1
export NEWCLAW_LMSTUDIO_BASE_URL=http://localhost:1234
export NEWCLAW_INTENT_CLASSIFIER_TIMEOUT=20

python3 app/cli.py submit \
  --requested-by qa_user \
  --task-kind auto \
  --request-text "billing-api 장애 대응 티켓을 생성해줘" \
  --metadata-json '{"service":"billing-api","severity":"low","time_window":"15m"}' \
  --json
```

참고:
- LM Studio provider는 `model: auto`로 등록되어 있어서 `/v1/models`의 첫 번째 loaded model을 사용한다.
- loaded model 응답이 느리면 `intent_classification.source=llm_error_fallback`으로 떨어질 수 있으니 `NEWCLAW_INTENT_CLASSIFIER_TIMEOUT`을 늘리거나 더 작은 모델을 먼저 올리는 편이 낫다.
- task planner baseline까지 local endpoint로 시험하려면:
```bash
export NEWCLAW_ENABLE_LLM_PLANNER=1
export NEWCLAW_LLM_PLANNER_TIMEOUT=20
```
- summary path까지 local endpoint로 시험하려면:
```bash
export NEWCLAW_ENABLE_LLM_SUMMARY=1
export NEWCLAW_OPENAI_BASE_URL=http://localhost:1234
```

제공 tool:
- `agent.submit`
- `agent.status`
- `agent.events`
- `approval.list`
- `approval.approve`
- `approval.reject`

3. 헬스체크
```bash
curl http://127.0.0.1:8000/health
```

4. 비IT 사용자 CLI 실행
```bash
python3 app/cli.py
```
기본 흐름:
- `Agent 요청 제출`
- `상태 조회`
- `이벤트 조회`
- `결과 확인`

5. 개발용 JWT 생성
```bash
python3 scripts/gen_dev_jwt.py --sub user_cli --role requester
```

6. PostgreSQL 마이그레이션(선택)
```bash
export NEWCLAW_DATABASE_URL="postgresql://user:pass@127.0.0.1:5432/new_claw"
bash scripts/migrate_postgres.sh up
```

7. 브라우저 스모크 도구 확인(선택)
```bash
command -v npx
```

8. Swagger/OpenAPI 브라우저 스모크 실행(선택)
```bash
bash scripts/run_browser_smoke.sh
```
- 기본값:
  - `NEWCLAW_BROWSER_SMOKE_BASE_URL=http://127.0.0.1:18080`
  - `NEWCLAW_BROWSER_SMOKE_AUTOSTART=1`
  - `NEWCLAW_BROWSER_SMOKE_SESSION=newclaw-browser-smoke`
- 종료코드:
  - `0`: PASS
  - `10`: 의존성 미충족(SKIP)
  - `1`: 실행/검증 실패(FAIL)
- 실패 시 증적 저장: `output/playwright/<timestamp>/`

9. Postgres 리허설 스모크 실행(선택)
```bash
export NEWCLAW_DATABASE_URL="postgresql://user:pass@127.0.0.1:5432/new_claw"
bash scripts/run_postgres_rehearsal.sh
```
- 종료코드:
  - `0`: PASS
  - `10`: 의존성/환경 미충족(SKIP)
  - `1`: 마이그레이션/런타임 검증 실패(FAIL)

10. IdP 키 회전 리허설 실행(선택)
```bash
bash scripts/run_idp_key_rotation_rehearsal.sh
```
- 상세 런북: `IDP_KEY_ROTATION_RUNBOOK.md`
- 운영 토큰/JWKS 입력 시 old/new 토큰 교체 검증까지 수행 가능

11. 로컬 Postgres 운영 제어(선택)
```bash
bash scripts/manage_local_postgres.sh status
bash scripts/manage_local_postgres.sh restart
bash scripts/manage_local_postgres.sh dsn
```
- 기본 대상: workspace 로컬 클러스터(`.local/pgdata`)
- 전역 시스템 Postgres는 제어하지 않음

## 12) Git 운영 기준
- 워크플로우 문서: `GIT_WORKFLOW.md`
- 워크트리 가이드: `GIT_WORKTREE_GUIDE.md`
- PR 템플릿: `.github/pull_request_template.md`
- 기본 브랜치: `main`
- 작업 브랜치: `codex/<topic>`
- 릴리즈 태그: `vMAJOR.MINOR.PATCH`

## 13) Codex 자동 순환
- 운영 가이드: `CODEX_AUTOMATION_CYCLE.md`
- 계획 QA 스크립트: `scripts/run_plan_qa.sh`
- 실행 스크립트: `scripts/run_dev_qa_cycle.sh`
- Stage 8 자체평가 스크립트: `scripts/run_stage8_self_eval.sh`
- Stage 8 readiness bundle: `scripts/run_stage8_readiness_bundle.sh`
- 마이크로 사이클 스크립트: `scripts/run_micro_cycle.sh`
- 전문가 에이전트 wrapper: `scripts/run_expert_agent_workflow.sh`
- priority campaign wrapper: `scripts/run_priority_campaign.sh`
- 전문가 에이전트 프로토콜: `EXPERT_AGENT_OPERATING_PROTOCOL_2026-03-13.md`
- priority campaign 프로토콜: `PRIORITY_CAMPAIGN_PROTOCOL_2026-03-15.md`
- 브라우저 스모크 스크립트: `scripts/run_browser_smoke.sh`
- Postgres 리허설 스크립트: `scripts/run_postgres_rehearsal.sh`
- 자동 반복 배치: `scripts/run_auto_cycle.sh`
- 문서감사 스크립트: `scripts/run_doc_audit.sh`
- 전문가 QA 스크립트: `scripts/run_expert_qa.sh`
- 다음단계 통합 파이프라인: `scripts/run_next_stage_pipeline.sh`
- 테스트:
  - `tests/test_spec_contract.py`
  - `tests/test_runtime_smoke.py`
  - `tests/test_stage7_contract.py`
  - `tests/test_stage8_contract.py`
  - `tests/test_agent_entrypoint_smoke.py`
  - `tests/test_incident_runtime_smoke.py`
  - `tests/test_auth_idp.py`

실행 예시:
```bash
bash scripts/run_dev_qa_cycle.sh 4
bash scripts/run_dev_qa_cycle.sh 8
bash scripts/run_stage8_self_eval.sh
bash scripts/run_stage8_readiness_bundle.sh
bash scripts/run_micro_cycle.sh status stage8-w2-001
bash scripts/run_expert_agent_workflow.sh status stage8-w5-022 8
bash scripts/run_expert_agent_workflow.sh sync stage8-w5-022 8
bash scripts/run_browser_smoke.sh
bash scripts/run_postgres_rehearsal.sh
bash scripts/run_auto_cycle.sh 8 10 3 --fix-cmd "<your-fix-command>"
bash scripts/run_plan_qa.sh NEXT_STAGE_PLAN_2026-02-24.md
bash scripts/run_next_stage_pipeline.sh 8 5 2 NEXT_STAGE_PLAN_2026-02-24.md
```

## 14) 보안형 에이전트 협업 아이디어
- 검토 문서: `SECURE_AGENT_COLLAB_ARCHITECTURE.md`
- 핵심:
  - 에이전트 private workspace 분리
  - broker 중재형 공유 채널 읽기/쓰기
  - local/api LLM 정책 라우팅

## 15) 최신 검토 결론
- 문서: `EXPERT_REVIEW_UPDATE_2026-02-24.md`
- 결론:
  - 현재 방향은 프로젝트 목적 달성에 유효
  - Stage 7 기준선(영속/인증/CI) 반영 완료, 운영 전 부하/장애복구 리허설 필요

## 16) 다음 단계 계획
- 계획 문서: `NEXT_STAGE_PLAN_2026-02-24.md`
- Stage 8 실행안: `INCIDENT_ORCHESTRATION_RAG_MCP_PLAN.md`
- Stage 8 체크리스트: `STAGE8_EXECUTION_CHECKLIST_2026-03-04.md`
- 전문가 운영 프로토콜: `EXPERT_AGENT_OPERATING_PROTOCOL_2026-03-13.md`
- Stage 8 상세 설계: `STAGE8_DETAILED_DESIGN_2026-03-04.md`
- 모델 라우팅 설정: `configs/model_registry.yaml`
- CI 품질게이트: `.github/workflows/quality-gate.yml`
