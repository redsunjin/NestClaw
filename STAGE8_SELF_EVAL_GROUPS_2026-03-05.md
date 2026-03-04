# Stage 8 Self-Evaluation Groups (2026-03-05)

## 목적
Stage 8 진행항목을 "자체평가 가능한 실행 그룹"으로 묶고, 각 그룹이 독립적으로 상태를 판정할 수 있도록 기준과 명령을 고정한다.

## 자체평가 원칙
- 그룹 단위 상태: `PASS`, `PENDING`, `FAIL`
- 그룹 산출물: 문서/코드/테스트/리포트 4종 증적
- 평가 주체:
  - 구현 리드: A02
  - 보안/정책 리뷰: A04
  - 품질 판정: A06
- 평가 리포트 위치: `reports/qa/stage8-self-eval-<timestamp>.md`

## 그룹 정의
### G1. Adapter Contract Foundation
범위:
- `app/incident_rag.py`
- `app/incident_mcp.py`
- `tests/test_incident_adapter_contract.py`
- MWU: `stage8-w2-001`

완료 조건:
- 어댑터 계약 테스트 PASS
- MWU 4단계 게이트 PASS

자체평가 명령:
```bash
python3 -m unittest tests.test_incident_adapter_contract
bash scripts/run_micro_cycle.sh status stage8-w2-001
```

### G2. Incident Orchestration Integration
범위:
- `app/main.py` incident 전용 intake/planner/executor 경로
- incident runtime dry-run 테스트
- MWU: `stage8-w3-001`

완료 조건:
- incident runtime 테스트 PASS
- 승인/차단/실패복구 상태 전이 검증 PASS

자체평가 명령:
```bash
python3 -m unittest tests.test_incident_runtime_smoke
bash scripts/run_micro_cycle.sh run stage8-w3-001 8
```

### G3. Policy & Approval Classification
범위:
- 승인 분류표 룰 코드화
- 정책 차단/승인 큐 연계
- MWU: `stage8-w3-002`

완료 조건:
- 정책 분류 단위 테스트 PASS
- 위험도별 상태 전이 검증 PASS

자체평가 명령:
```bash
python3 -m unittest tests.test_incident_policy_gate
bash scripts/run_micro_cycle.sh run stage8-w3-002 8
```

### G4. Quality Gate & Sandbox Readiness
범위:
- Stage 8 CI 품질게이트 통합
- Sandbox E2E 증적 확보
- MWU: `stage8-w4-001`

완료 조건:
- `scripts/run_next_stage_pipeline.sh 8` PASS
- Sandbox E2E 리포트 존재

자체평가 명령:
```bash
bash scripts/run_next_stage_pipeline.sh 8 2 1 NEXT_STAGE_PLAN_2026-02-24.md
```

## 점수 규칙
- `PASS`: 2점
- `PENDING`: 1점
- `FAIL`: 0점
- Stage 8 준비도 점수 = `sum(group_score) / 8 * 100`

## 현재 초기 판정 (2026-03-05)
- readiness_score: `5/8 (62%)` (`scripts/run_stage8_self_eval.sh` baseline 실행 결과)
- G1: PASS
- G2: PENDING (`stage8-w3-001`은 `IMPLEMENT_READY`, runtime smoke 미구현)
- G3: PENDING (정책 분류 테스트 및 MWU 미착수)
- G4: PENDING (Stage 8 CI wiring/Sandbox 증적 미완료)
