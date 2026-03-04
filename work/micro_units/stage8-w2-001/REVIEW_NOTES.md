# Review Notes

## Security / Policy Review
- 외부 호출은 스켈레톤 단계에서 실실행하지 않고 인터페이스/검증 계층만 노출해야 한다.
- `payload`/`actor_context` 로그 출력 시 `token`, `password`, `secret` 키는 마스킹 규칙을 따른다.
- 승인 전 고위험 액션 실행 금지 원칙을 코드 주석/문서에 명시한다.
- 정책 위반 시 `BLOCKED_POLICY` 경로와 충돌하지 않도록 main 통합 전 단위 계약을 고정한다.

## Architecture / Workflow Review
- `STAGE8_DETAILED_DESIGN_2026-03-04.md`의 인터페이스 계약(섹션 9)을 단일 진실원천으로 사용한다.
- 현재 스텝의 목적은 adapter skeleton 분리이므로 orchestration 결합은 다음 MWU로 분리한다.
- 파일 분리는 다음 의존 역전을 보장한다:
  - main/orchestrator -> incident_rag, incident_mcp
  - incident adapters는 정책 결정을 직접 수행하지 않음

## QA Gate Review
- Plan/Review 단계 완료 게이트: `bash scripts/run_micro_cycle.sh gate-plan stage8-w2-001`, `gate-review`
- 구현 완료 후 게이트:
  - `bash scripts/run_micro_cycle.sh gate-implement stage8-w2-001`
  - `bash scripts/run_micro_cycle.sh gate-evaluate stage8-w2-001 8`
- Stage 8 기준선 유지 확인:
  - `python3 -m unittest tests.test_stage8_contract`
  - `bash scripts/run_dev_qa_cycle.sh 8`

## Review Verdict
- 조건부 승인 (Approved with Guardrails)
- 조건:
  1. 외부 네트워크 실호출 코드를 넣지 않는다.
  2. 민감정보 마스킹 규칙 위반 시 구현 반려한다.
  3. 구현 완료 후 Evaluate gate PASS를 확인한다.
