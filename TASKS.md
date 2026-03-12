# 실행 체크리스트 (Step 기반)

## 목적
`README.md`와 `FEASIBILITY_VALIDATION_REPORT.md`의 가드레일을 실제 구현 태스크로 전환한다.

## 운영 규칙
- 체크박스는 완료 시점에만 변경한다.
- 확장 기능은 품질 게이트 통과 후에만 진행한다.
- 위험 액션은 항상 승인 단계로 보낸다.
- 각 단계는 착수 전에 담당 전문가 그룹이 상세계획을 수립하고, 사전 검토 승인 후에만 실행한다.

## Step 1. API/상태머신 기초
- [x] `/task/create` 엔드포인트 스펙 고정 (`API_CONTRACT.md`)
- [x] `/task/run` 엔드포인트 스펙 고정 (`API_CONTRACT.md`)
- [x] `/task/status` 엔드포인트 스펙 고정 (`API_CONTRACT.md`)
- [x] 상태 코드 정의: `READY`, `RUNNING`, `FAILED_RETRYABLE`, `NEEDS_HUMAN_APPROVAL`, `DONE` (`API_CONTRACT.md`, `STATE_MACHINE.md`)
- [x] 상태 전이 규칙 문서화 (`STATE_MACHINE.md`)

완료 기준:
- 단일 Task ID로 생성/실행/상태 조회가 가능해야 함

## Step 2. 오케스트레이션 체인
- [x] Planner 구현 (입력 -> 실행 계획, `app/main.py`)
- [x] Executor 구현 (계획 -> 실행, `app/main.py`)
- [x] Reviewer 구현 (결과 검토, `app/main.py`)
- [x] Reporter 구현 (최종 보고서 생성, `app/main.py`)
- [x] 체인 연결: `planner -> executor -> reviewer -> reporter` (`app/main.py`)

완료 기준:
- 단일 입력에서 최종 보고서까지 end-to-end 동작

## Step 3. 정책/권한
- [x] 화이트리스트 경로 정의 (`POLICY_WHITELIST.md`)
- [x] 금지 명령 목록 정의 (`POLICY_WHITELIST.md`)
- [x] RBAC 역할 정의 (요청자/검토자/승인자/관리자, `app/main.py`, `API_CONTRACT.md`)
- [x] 정책 위반 시 `BLOCKED_POLICY` 이벤트 로깅 (`app/main.py`, `POLICY_WHITELIST.md`)

완료 기준:
- 비허용 액션이 실행되지 않고 차단 로그가 남아야 함

## Step 4. 실패 복구/승인
- [x] 실패 시 재시도 1회 구현 (`app/main.py`)
- [x] 재시도 실패 시 `NEEDS_HUMAN_APPROVAL` 전환 (`app/main.py`)
- [x] 승인 큐 조회 기능 추가 (`GET /api/v1/approvals`, `app/main.py`)
- [x] 승인/반려 이력 로그 기록 (`app/main.py`, `APPROVAL_QUEUE_MODEL.md`)

완료 기준:
- 실패 경로가 자동 복구 또는 승인 대기로 일관되게 전환

## Step 5. 비IT 사용자 UX
- [x] 템플릿 선택형 입력 화면/CLI 구현 (`app/cli.py`)
- [x] 자유 프롬프트 대신 템플릿 필드 기반 입력 적용 (`app/cli.py`)
- [x] 상태 메시지 표준화 (현재 상태/다음 액션/필요 승인) (`app/cli.py`)
- [x] 결과 확인 화면 단순화 (`app/cli.py`)
- [x] 단일 agent 진입 CLI로 기본 흐름 통합 (`app/cli.py`, `/api/v1/agent/*`)

완료 기준:
- 비IT 사용자 기준으로 생성/실행/상태/결과 4동작을 수행 가능

## Step 6. 검증 게이트
- [x] 정상 시나리오 테스트 (`tests/test_runtime_smoke.py`)
- [x] 실패 시나리오 테스트 (`tests/test_runtime_smoke.py`)
- [x] 차단 시나리오 테스트 (`tests/test_runtime_smoke.py`)
- [x] 로그 누락 점검 (`GET /api/v1/task/events/{task_id}`, `tests/test_runtime_smoke.py`)
- [x] 정책 위반 0건 확인 (`GET /api/v1/audit/summary`, `policy_bypass_events=0`)

완료 기준:
- 회귀 테스트 통과 + 정책 위반 0 + 로그 누락 0
주의:
- 런타임 시나리오는 `fastapi` 테스트 런타임이 설치된 환경에서 최종 확인한다.

## Automation
- [x] 개발/QA 순환 스크립트 추가 (`scripts/run_dev_qa_cycle.sh`)
- [x] 정적 스펙 계약 테스트 추가 (`tests/test_spec_contract.py`)
- [x] 런타임 스모크 테스트 추가 (`tests/test_runtime_smoke.py`)
- [x] 순환 운영 가이드 문서화 (`CODEX_AUTOMATION_CYCLE.md`)

## Stage 7 착수 (운영 전환 준비)
- [x] 다음 단계 실행계획 수립 (`NEXT_STAGE_PLAN_2026-02-24.md`)
- [x] 계획 QA 자동화 (`scripts/run_plan_qa.sh`)
- [x] 문서 정합성 감사 자동화 (`scripts/run_doc_audit.sh`)
- [x] 전문가 QA 리포트 자동화 (`scripts/run_expert_qa.sh`)
- [x] 다음단계 통합 파이프라인 추가 (`scripts/run_next_stage_pipeline.sh`)
- [x] CI 품질게이트 워크플로우 추가 (`.github/workflows/quality-gate.yml`)
- [x] 모델 레지스트리 초안 추가 (`configs/model_registry.yaml`)
- [x] 저장소 영속화(DB) 어댑터 구현 (`app/persistence.py`, SQLite)
- [x] 실운영 인증 계층(JWT/SSO) 연결 (`app/auth.py`, `app/main.py`)
- [x] PostgreSQL 어댑터 및 마이그레이션 스크립트 (`app/persistence.py`, `migrations/postgres/001_init.sql`, `scripts/migrate_postgres.sh`)
- [x] 외부 IdP(SSO) 검증 연동(서명키/토큰 검증 체계) (`app/auth.py`, `tests/test_auth_idp.py`)
- [x] 운영 Postgres 연결 리허설 스크립트 추가 (`scripts/run_postgres_rehearsal.sh`, `scripts/run_dev_qa_cycle.sh`)
- [x] IdP 키 회전 시나리오 회귀 테스트 추가 (`tests/test_auth_idp.py`)
- [x] IdP 키 회전 운영 런북 문서화 (`IDP_KEY_ROTATION_RUNBOOK.md`)
- [x] IdP 키 회전 리허설 자동화 스크립트 추가 (`scripts/run_idp_key_rotation_rehearsal.sh`)
- [x] 로컬 Postgres 안전 운영 스크립트 추가 (`scripts/manage_local_postgres.sh`)

## Stage 8 착수 (킬러 컨텐츠: 운영장애 대응 오케스트레이션)
### A) 설계/계약 고정 (완료: 2026-03-04)
- [x] Stage 8 목표/범위/성공지표 고정 (`INCIDENT_ORCHESTRATION_RAG_MCP_PLAN.md`)
- [x] 외부 업무지식 RAG 연동 계약 고정 (입력/출력/신뢰도 필드, `STAGE8_DETAILED_DESIGN_2026-03-04.md`)
- [x] 시스템분석 RAG 연동 계약 고정 (신호/근거/컴포넌트 필드, `STAGE8_DETAILED_DESIGN_2026-03-04.md`)
- [x] Redmine MCP 메서드 맵 고정 (`issue.create/update/add_comment/assign/transition`, `STAGE8_DETAILED_DESIGN_2026-03-04.md`)
- [x] 장애 전용 액션 카드 스키마 정의 (위험도/승인필요여부/근거링크, `STAGE8_DETAILED_DESIGN_2026-03-04.md`)
- [x] 승인 분류표 확정 (자동실행 가능 vs 승인필수, `STAGE8_DETAILED_DESIGN_2026-03-04.md`)
- [x] Incident 전용 planner/executor 경로 상세 설계 (`STAGE8_DETAILED_DESIGN_2026-03-04.md`)
- [x] Dry-run E2E 시나리오 작성 (티켓 생성 시뮬레이션, `STAGE8_DETAILED_DESIGN_2026-03-04.md`)
- [x] Sandbox E2E 시나리오 작성 (테스트 Redmine 프로젝트, `STAGE8_DETAILED_DESIGN_2026-03-04.md`)
- [x] Stage 8 품질게이트 정의 (정상/차단/승인대기/실패복구, `STAGE8_DETAILED_DESIGN_2026-03-04.md`)
- [x] Stage 8 실행 체크리스트 작성 (`STAGE8_EXECUTION_CHECKLIST_2026-03-04.md`)
- [x] Stage 8 주차별 스케줄 고정 (`NEXT_STAGE_PLAN_2026-02-24.md`)
- [x] Stage 8 마이크로 작업 프로토콜 선언 (`MICRO_AGENT_WORKFLOW.md`)
- [x] 마이크로 사이클 자동화 스크립트 추가 (`scripts/run_micro_cycle.sh`)
- [x] 1번 구현작업 MWU 생성 및 4단계 게이트 통과 (`work/micro_units/stage8-w2-001/`)

### B) 구현/검증 (진행 필요)
- [x] RAG 클라이언트 인터페이스 2종 스켈레톤 구현 (`app/incident_rag.py`)
- [x] Redmine MCP 실행 어댑터 스켈레톤 구현 (`app/incident_mcp.py`)
- [x] Incident Intake + Action Planner 경로 구현 (`app/main.py`)
- [x] 승인 분류표를 정책 룰로 구현 (`POLICY_WHITELIST.md`, `app/main.py`, `app/incident_policy.py`)
- [x] Dry-run E2E 자동 테스트 추가 (`tests/test_incident_runtime_smoke.py`)
- [x] 단일 agent facade 진입점 추가 (`app/main.py`, `tests/test_agent_entrypoint_smoke.py`, `app/cli.py`)
- [x] Sandbox E2E 리허설 증적 리포트 작성 (`reports/qa/stage8-sandbox-e2e-20260306T140858Z.md`, QA worktree)
- [x] Stage 8 품질게이트를 CI 파이프라인에 통합 (`.github/workflows/quality-gate.yml`)

### C) Stage 8 실행 스케줄 (2026-03-05 ~ 2026-04-24)
- [ ] 2026-03-05 ~ 2026-03-06: 기준선 고정 (문서/백로그/오너 확정)
- [ ] 2026-03-09 ~ 2026-03-13: 계약 고정 (Incident/RAG/MCP/승인 분류)
- [ ] 2026-03-16 ~ 2026-03-20: 어댑터 스켈레톤 구현
- [ ] 2026-03-23 ~ 2026-03-27: Incident 오케스트레이션 결합
- [ ] 2026-03-30 ~ 2026-04-03: Stage 8 품질게이트 자동화
- [ ] 2026-04-06 ~ 2026-04-10: Sandbox 운영 검증
- [ ] 2026-04-13 ~ 2026-04-24: 파일럿/안정화 및 Go/No-Go 판단

### D) 자체평가 그룹 운영 (2026-03-05)
- [x] 자체평가 그룹 문서 고정 (`STAGE8_SELF_EVAL_GROUPS_2026-03-05.md`)
- [x] 그룹 자동평가 스크립트 추가 (`scripts/run_stage8_self_eval.sh`)
- [x] baseline 자체평가 실행 (G1 PASS, G2~G4 PENDING)
- [x] G2 MWU(`stage8-w3-001`) 생성 및 완료
- [x] G2(Incident Orchestration Integration) PASS
- [x] G3(Policy & Approval Classification) PASS
- [x] G4 MWU(`stage8-w4-001`) 생성 및 완료
- [x] G4(Quality Gate & Sandbox Readiness) PASS

### E) Live Rehearsal Follow-up (2026-03-07)
- [x] Live rehearsal MWU(`stage8-w5-001`) 생성
- [x] `mcp-live` 실행 모드 분리 (`app/main.py`)
- [x] Redmine MCP live bridge 추가 (`app/incident_mcp.py`)
- [x] live rehearsal runbook/script 추가 (`STAGE8_LIVE_REHEARSAL_RUNBOOK_2026-03-07.md`, `scripts/run_stage8_live_rehearsal.sh`)
- [ ] 외부 sandbox credential 기반 live rehearsal PASS 증적 확보 (QA worktree)

### F) Agent Tool Surface Follow-up (2026-03-12)
- [x] 서비스 계층 분리 (`app/main.py` -> `app/services/orchestration_service.py`)
- [ ] 비대화형 tool CLI 추가 (`submit/status/events/approve/reject --json`)
- [ ] MCP server 추가 (`agent.submit`, `agent.status`, `agent.events`, `approval.list/approve/reject`)
- [ ] `configs/model_registry.yaml` runtime loader 연결 및 provider selection logging 추가
- [ ] `task_kind=auto`를 heuristic에서 LLM intent classifier로 고도화
- [ ] 최소 operator UI 설계 초안 작성
- [ ] 방향 문서 고정 (`AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md`)

## 즉시 시작 5개
1. [x] API 계약서 초안 작성 (`API_CONTRACT.md`)
2. [x] 상태 전이 다이어그램 작성 (`STATE_MACHINE.md`)
3. [x] 정책 화이트리스트 초안 작성 (`POLICY_WHITELIST.md`)
4. [x] 승인 큐 데이터 모델 정의 (`APPROVAL_QUEUE_MODEL.md`)
5. [x] 템플릿 1종(회의요약) 연결 테스트 (`tests/test_runtime_smoke.py`)
