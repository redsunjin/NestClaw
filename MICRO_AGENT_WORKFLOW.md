# Micro Agent Workflow Protocol

## 목적
Stage 8 구현 작업을 `계획 -> 검토 -> 구현 -> 평가`의 마이크로 단위로 표준화하고, 각 전문 에이전트가 같은 게이트 기준으로 자동 실행할 수 있게 한다.

## 선언 (2026-03-04)
- 모든 Stage 8 구현 작업은 Micro Work Unit(MWU) 단위로 운영한다.
- MWU는 `work/micro_units/<unit_id>/` 디렉터리로 관리한다.
- 각 단위는 4단계 게이트를 통과해야 다음 단계로 이동한다.
- 최종 승인권자는 A01(Product Owner), 품질 게이트 책임자는 A06(QA Reliability)다.

## 역할 분담 (전문 에이전트 기준)
| 단계 | 리드 | 필수 협의 |
|---|---|---|
| Plan | A01 | A02, A03 |
| Review | A04 | A06, A07 |
| Implement | A02 | A03 |
| Evaluate | A06 | A01, A08 |

## 단계 정의
### 1) Plan
산출물:
- `PLAN_NOTES.md`
- 범위/비범위, 수용기준, 리스크, 테스트 계획

게이트:
- 필수 섹션 존재
- `TODO/TBD` 미포함

### 2) Review
산출물:
- `REVIEW_NOTES.md`
- 보안/정책/권한/테스트 관점 검토 결과

게이트:
- 필수 섹션 존재
- `TODO/TBD` 미포함
- Stage 8 계약 테스트 통과(`tests/test_stage8_contract.py`)

### 3) Implement
산출물:
- 코드 변경 + `IMPLEMENT_NOTES.md`
- 변경 파일 목록, 롤백 방법, 잔여 리스크

게이트:
- 구현 노트 필수 섹션 존재
- `TODO/TBD` 미포함
- 변경 파일이 실제로 존재

### 4) Evaluate
산출물:
- QA 리포트 + `EVALUATE_NOTES.md`

게이트:
- `scripts/run_dev_qa_cycle.sh 8` 통과
- 실패/스킵 원인 기록
- 다음 액션 또는 완료 판정 기록

## 표준 실행 명령
```bash
# 1) 유닛 생성
bash scripts/run_micro_cycle.sh init <unit_id> "<goal>" 8

# 2) 단계 게이트
bash scripts/run_micro_cycle.sh gate-plan <unit_id>
bash scripts/run_micro_cycle.sh gate-review <unit_id>
bash scripts/run_micro_cycle.sh gate-implement <unit_id>
bash scripts/run_micro_cycle.sh gate-evaluate <unit_id> 8

# 3) 전체 게이트(구현 노트까지 작성된 이후)
bash scripts/run_micro_cycle.sh run <unit_id> 8
```

## 최초 적용 유닛
- `stage8-w2-001`
- 목표: `app/incident_rag.py`, `app/incident_mcp.py` 스켈레톤 구현
- 경로: `work/micro_units/stage8-w2-001/`

## 운영 규칙
- 하나의 MWU는 하나의 명확한 구현 목표만 가진다.
- MWU 완료 전 다른 MWU와 병합하지 않는다.
- 모든 게이트 리포트는 `work/micro_units/<unit_id>/reports/`에 저장한다.
