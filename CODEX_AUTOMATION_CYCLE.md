# Codex Dev-QA 순환 운영 가이드

## 목적
목표/스펙(`README.md`, `TASKS.md`) 기준으로 개발과 QA를 자동 순환하고,
지정한 단계(`Step N`)까지 도달 가능한지 자동 판정한다.

## 핵심 개념
- 입력: 목표 단계(1~6)
- 실행: 단계별 게이트 체크(정적 검증 + 테스트)
- 출력: QA 리포트(`reports/qa/cycle-<timestamp>.md`)
- 종료: 실패 0이면 해당 단계까지 통과

## 실행 명령
```bash
bash scripts/run_dev_qa_cycle.sh 4
```

예시:
- Step 4까지 판정: `bash scripts/run_dev_qa_cycle.sh 4`
- Step 6까지 판정: `bash scripts/run_dev_qa_cycle.sh 6`

## 자동 반복 배치
반복 실행 + 실패 시 수정 명령을 훅으로 연결하려면:

```bash
bash scripts/run_auto_cycle.sh 6 10 3 --fix-cmd "<your-fix-command>"
```

파라미터:
- `target-stage`: 1~6
- `max-rounds`: 최대 반복 횟수
- `sleep-seconds`: 라운드 간 대기
- `--fix-cmd`: 실패 라운드 뒤 실행할 수정 명령

예시:
```bash
bash scripts/run_auto_cycle.sh 4
bash scripts/run_auto_cycle.sh 6 5 2 --fix-cmd "python3 -m unittest tests.test_spec_contract"
```

## 문서감사 + 전문가QA + 다음단계 파이프라인
한 번에 실행하려면:
```bash
bash scripts/run_next_stage_pipeline.sh 6 5 2
```

구성:
1. `scripts/run_plan_qa.sh`
2. `scripts/run_doc_audit.sh`
3. `scripts/check_model_registry.sh`
4. `scripts/run_expert_qa.sh`
5. `scripts/run_auto_cycle.sh`

## 단계별 자동 게이트
### Stage 1
- API 파일 문법 검증
- `create/run/status` 엔드포인트 존재 확인

### Stage 2
- 오케스트레이션 체인(`planner/executor/reviewer/reporter`) 존재 확인

### Stage 3
- 정책 차단 이벤트(`BLOCKED_POLICY`) 존재
- 정책 문서 존재

### Stage 4
- 재시도/승인 전환 로직 존재
- 승인 관련 API 존재

### Stage 5
- 비IT 템플릿/테스트 계획 문서 존재
- UX 구현 파일(`app/cli.py`) 존재 여부 확인

### Stage 6
- 정적 계약 테스트(`tests/test_spec_contract.py`)
- 런타임 스모크 테스트(`tests/test_runtime_smoke.py`, 의존성 있을 때 실행)

## Codex 자동 순환 방식 (권장)
1. 목표 단계 지정 (예: `Step 5`)
2. Codex가 미완료 항목 구현
3. `run_dev_qa_cycle.sh` 실행
4. 실패 항목 수정
5. 다시 실행
6. 전부 통과 시 커밋 + 다음 단계로 이동

## 커밋 규칙
- 개발 변경: `feat(...)`
- 테스트/품질: `test(...)`
- 문서: `docs(...)`
- 운영/스크립트: `chore(...)`

## 주의
- Stage 5는 현재 `app/cli.py`가 없으면 실패하게 설계되어 있다.
- Stage 6 런타임 테스트는 `fastapi/pydantic/uvicorn` 설치가 필요하다.
