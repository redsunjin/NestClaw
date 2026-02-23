# 로컬 업무 위임 오케스트레이션 (기본문서)

## 문서 목적
이 문서는 전문가 그룹 검토를 바탕으로 프로젝트의 목적, 개발 계획, 현실적 접근 방안을 정의하는 기본 기준 문서다.

상세 검토 원문은 `REVIEW_REPORT.md`를 따른다.

## 1) 프로젝트 목적
### 1.1 핵심 목적
- 로컬 환경에서 안전하게 동작하는 **직장 동료형 업무 위임 오케스트레이션**을 구현한다.
- 사용자는 지시자, 시스템은 계획/실행/검토/보고를 수행한다.

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
- 비IT 업무 템플릿 3종: `NON_IT_WORK_TEMPLATES.md`
- API 계약서 초안: `API_CONTRACT.md`
- 상태 전이 문서: `STATE_MACHINE.md`
- 정책 화이트리스트 초안: `POLICY_WHITELIST.md`
- 승인 큐 데이터 모델: `APPROVAL_QUEUE_MODEL.md`
- 회의요약 템플릿 테스트 계획: `TEMPLATE_MEETING_SUMMARY_TEST_PLAN.md`

## 10) 현재 구현 상태
- API 스켈레톤 구현 완료:
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

코드 위치:
- 서버: `app/main.py`
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

3. 헬스체크
```bash
curl http://127.0.0.1:8000/health
```

4. 비IT 사용자 CLI 실행
```bash
python3 app/cli.py
```

5. 개발용 JWT 생성
```bash
python3 scripts/gen_dev_jwt.py --sub user_cli --role requester
```

6. PostgreSQL 마이그레이션(선택)
```bash
export NEWCLAW_DATABASE_URL="postgresql://user:pass@127.0.0.1:5432/new_claw"
bash scripts/migrate_postgres.sh up
```

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
- 자동 반복 배치: `scripts/run_auto_cycle.sh`
- 문서감사 스크립트: `scripts/run_doc_audit.sh`
- 전문가 QA 스크립트: `scripts/run_expert_qa.sh`
- 다음단계 통합 파이프라인: `scripts/run_next_stage_pipeline.sh`
- 테스트:
  - `tests/test_spec_contract.py`
  - `tests/test_runtime_smoke.py`
  - `tests/test_stage7_contract.py`
  - `tests/test_auth_idp.py`

실행 예시:
```bash
bash scripts/run_dev_qa_cycle.sh 4
bash scripts/run_auto_cycle.sh 7 10 3 --fix-cmd "<your-fix-command>"
bash scripts/run_plan_qa.sh NEXT_STAGE_PLAN_2026-02-24.md
bash scripts/run_next_stage_pipeline.sh 7 5 2 NEXT_STAGE_PLAN_2026-02-24.md
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
- 모델 라우팅 설정: `configs/model_registry.yaml`
- CI 품질게이트: `.github/workflows/quality-gate.yml`
