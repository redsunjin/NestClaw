# 실행 체크리스트 (Step 기반)

## 목적
`README.md`와 `FEASIBILITY_VALIDATION_REPORT.md`의 가드레일을 실제 구현 태스크로 전환한다.

## 운영 규칙
- 체크박스는 완료 시점에만 변경한다.
- 확장 기능은 품질 게이트 통과 후에만 진행한다.
- 위험 액션은 항상 승인 단계로 보낸다.

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
- [x] 문서 정합성 감사 자동화 (`scripts/run_doc_audit.sh`)
- [x] 전문가 QA 리포트 자동화 (`scripts/run_expert_qa.sh`)
- [x] 다음단계 통합 파이프라인 추가 (`scripts/run_next_stage_pipeline.sh`)
- [x] CI 품질게이트 워크플로우 추가 (`.github/workflows/quality-gate.yml`)
- [x] 모델 레지스트리 초안 추가 (`configs/model_registry.yaml`)
- [ ] 저장소 영속화(DB) 어댑터 구현
- [ ] 실운영 인증 계층(JWT/SSO) 연결

## 즉시 시작 5개
1. [x] API 계약서 초안 작성 (`API_CONTRACT.md`)
2. [x] 상태 전이 다이어그램 작성 (`STATE_MACHINE.md`)
3. [x] 정책 화이트리스트 초안 작성 (`POLICY_WHITELIST.md`)
4. [x] 승인 큐 데이터 모델 정의 (`APPROVAL_QUEUE_MODEL.md`)
5. [x] 템플릿 1종(회의요약) 연결 테스트 (`tests/test_runtime_smoke.py`)
