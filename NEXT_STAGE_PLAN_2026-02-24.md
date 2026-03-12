# Next Stage Plan (2026-02-24)

## 목표
현재 PoC를 "운영 전환 가능 베타"로 끌어올린다.

## Stage 7 범위
1. 인증 고도화
- 헤더 기반 RBAC -> 토큰/JWT 검증 계층 추가

2. 영속 저장소 전환
- in-memory -> SQLite/PostgreSQL 어댑터
- `tasks`, `task_events`, `approval_queue`, `approval_actions` 저장

3. QA/게이트 고정
- CI에서 문서 감사 + 스펙 테스트 + 단계 게이트 강제

4. 모델 라우팅 스켈레톤
- local/api LLM 등록 구조와 라우팅 정책 파일 추가

## Stage 8 범위 (신규)
1. 운영장애 대응 오케스트레이션
- Incident 입력 -> 컨텍스트 집계 -> 액션 카드 -> 승인/실행 -> 복구보고 체인 추가

2. 외부 RAG 통합
- 업무 지식 RAG + 시스템 분석 RAG를 컨텍스트 집계 계층으로 연결

3. MCP 실행 계층 통합
- Redmine MCP를 통한 티켓 생성/갱신/담당자 지정/상태전환 자동화

4. 운영형 품질 게이트
- 장애 시나리오 E2E(정상/차단/승인대기/실패복구) 기준선 고정

## 완료 기준
- 서비스 재시작 후 Task/로그/승인 데이터 유지
- RBAC가 인증 토큰 정보 기반으로 작동
- PR마다 자동 품질 게이트 통과 필수
- 모델 라우팅 정책 파일 기준으로 provider 선택 로그 기록

## Stage 8 완료 기준 (신규)
- 외부 RAG 근거를 포함한 액션 카드가 생성되어야 함
- 승인 정책 없이 고위험 액션이 실행되지 않아야 함
- Redmine MCP로 장애 티켓 생명주기(생성/갱신/전환)가 재현되어야 함
- 장애 E2E 회귀 세트가 CI/게이트에서 반복 실행 가능해야 함

## 실행 순서
1. CI 파이프라인 추가 (즉시)
2. 모델 라우팅 설정 파일/로더 추가 (즉시)
3. 저장소 어댑터 인터페이스 분리 (다음)
4. DB 구현 및 마이그레이션 (다음)
5. JWT 인증 계층 연결 (다음)

## 진행 현황 업데이트 (2026-02-24)
- 완료:
  - CI 파이프라인 추가
  - 모델 라우팅 설정 파일 추가
  - SQLite 영속 저장소 어댑터 추가
  - PostgreSQL 어댑터 + 마이그레이션 스크립트
  - Postgres 리허설 스모크 스크립트 + Stage7 게이트 연동
  - JWT/SSO 인증 경로 추가
  - 외부 IdP 연동 검증(JWKS 기반 서명 검증)
  - IdP JWKS 키 회전 시나리오 회귀 테스트 추가
- 잔여:
  - 운영 환경 DB URL로 `scripts/run_postgres_rehearsal.sh` 실행 검증
  - 실제 IdP 키 교체 절차와 동일한 운영 키 회전 리허설

## 진행 현황 업데이트 (2026-03-03)
- 완료:
  - 로컬 운영형 DB URL로 `scripts/run_postgres_rehearsal.sh` 실행 검증
  - IdP JWKS 키 회전 시나리오 리허설(신규 kid 허용/기존 kid 차단) 재검증
- 잔여:
  - 실제 사내 IdP 운영 절차와 동일한 키 교체 런북 리허설

## 진행 현황 업데이트 (2026-03-04)
- 완료:
  - IdP 키 회전 런북 문서화 (`IDP_KEY_ROTATION_RUNBOOK.md`)
  - IdP 키 회전 리허설 스크립트 추가 (`scripts/run_idp_key_rotation_rehearsal.sh`)
  - 로컬 Postgres 운영 제어 스크립트 추가 (`scripts/manage_local_postgres.sh`)
- 잔여:
  - 실제 사내 IdP 운영 토큰/JWKS 기반 실리허설 증적 적재

## Stage 8 진행 현황 업데이트 (2026-03-04)
- 완료:
  - Stage 8 기준 문서 초안 작성 (`INCIDENT_ORCHESTRATION_RAG_MCP_PLAN.md`)
  - Stage 8 실행 체크리스트 작성 (`STAGE8_EXECUTION_CHECKLIST_2026-03-04.md`)
  - Stage 8 상세 설계 고정 (`STAGE8_DETAILED_DESIGN_2026-03-04.md`)
  - Stage 8 마이크로 작업 프로토콜 선언 및 자동화 (`MICRO_AGENT_WORKFLOW.md`, `scripts/run_micro_cycle.sh`)
  - 1번 구현작업 MWU 생성 및 Plan/Review 게이트 통과 (`work/micro_units/stage8-w2-001/`)
  - 1번 구현작업 MWU 구현/평가 게이트 통과 (`app/incident_rag.py`, `app/incident_mcp.py`)
  - Stage 8 자체평가 그룹 문서/스크립트 추가 및 baseline 실행 (`STAGE8_SELF_EVAL_GROUPS_2026-03-05.md`, `scripts/run_stage8_self_eval.sh`)
  - 2번 구현작업 MWU(`stage8-w3-001`) 생성 및 Plan/Review 게이트 통과
- 잔여:
  - Incident 전용 오케스트레이션 구현/검증
  - Sandbox 운영 증적 확보 및 파일럿 Go/No-Go

## Stage 8 진행 현황 업데이트 (2026-03-06)
- 완료:
  - G1~G4 grouped self-eval PASS (`reports/qa/stage8-self-eval-20260306T141522Z.md`, QA worktree)
  - Incident runtime dry-run/정책 분류/CI 품질게이트/rehearsal 스크립트 고정
  - Stage 8 종료 요약 문서 작성 (`STAGE8_CLOSEOUT_SUMMARY_2026-03-06.md`)
- 잔여:
  - 실제 외부 sandbox live rehearsal
  - 파일럿/안정화 및 Go/No-Go 판단

## Stage 8 진행 현황 업데이트 (2026-03-07)
- 완료:
  - live rehearsal 후속 MWU 생성 (`work/micro_units/stage8-w5-001/`)
  - incident runtime `mcp-live` 모드 분리
  - Redmine MCP live bridge / runbook / rehearsal script 추가
- 잔여:
  - 외부 sandbox credential이 있는 QA worktree에서 live rehearsal `PASS` 증적 확보
  - 파일럿 대상 서비스/팀 확정 및 Go/No-Go 패키지 작성

## Agent 제품화 방향 업데이트 (2026-03-12)
- 완료:
  - 단일 agent facade 경로 추가 (`app/main.py`)
  - 기본 사용자 진입점을 `agent submit/status/events`로 통합 (`app/cli.py`, `API_CONTRACT.md`)
  - agent facade runtime smoke 및 QA cycle 고정 (`tests/test_agent_entrypoint_smoke.py`, `scripts/run_dev_qa_cycle.sh`)
  - `task_kind=auto` 경로를 LLM intent classifier + heuristic fallback으로 고도화 (`app/intent_classifier.py`)
  - LM Studio local provider 등록 및 OpenAI-compatible local adapter 연결 (`http://localhost:1234`)
- 현재 진단:
  - 현재 제품은 "오케스트레이션 백엔드 + 단일 facade + classifier" 수준이다.
  - MCP server, model registry runtime selection logging, intent classification provenance, LM Studio local adapter까지는 연결됐다.
  - 아직 실제 provider invocation, live RAG, 범용 tool planning, operator UI는 없다.
- 다음 우선순위:
  1. model registry selection을 실제 provider invocation과 연결
  2. action-card / tool planning 공통 루프를 정리
  3. 최소 operator UI 설계/구현
  4. sandbox/live rehearsal env를 넣어 운영 검증을 닫기
- 기준 문서:
  - `AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md`

## 리스크
- 네트워크 제약 환경에서 런타임 테스트 일부 skip 가능
- DB 전환 시 기존 API 응답 포맷 회귀 위험

## 대응
- 계약 테스트 유지/강화
- 상태 전이 테스트를 DB/메모리 공용으로 실행
- 자동 배치(`run_auto_cycle`)로 회귀 감시

## Stage 8 실행 스케줄 업데이트 (2026-03-04)
1. 2026-03-05 ~ 2026-03-06: 기준선 고정 (백로그/오너/대상 서비스)
2. 2026-03-09 ~ 2026-03-13: 계약 고정 (Incident/RAG/MCP/승인 분류)
3. 2026-03-16 ~ 2026-03-20: 어댑터 스켈레톤 구현
4. 2026-03-23 ~ 2026-03-27: Incident 오케스트레이션 결합
5. 2026-03-30 ~ 2026-04-03: Stage 8 품질게이트 자동화
6. 2026-04-06 ~ 2026-04-10: Sandbox 운영 검증
7. 2026-04-13 ~ 2026-04-24: 파일럿/안정화 및 Go/No-Go 판단
