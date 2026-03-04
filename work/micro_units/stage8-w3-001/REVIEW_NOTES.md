# Review Notes

## Security / Policy Review
- incident 경로에서도 고위험 액션은 기본 승인 필수 원칙을 유지한다.
- `actor_context`는 기존 인증 경로를 재사용하며 anonymous 실행은 금지한다.
- incident payload 로그는 민감필드 마스킹 원칙을 적용한다.
- dry-run 기본값을 유지하고 live 모드 진입은 별도 승인 MWU로 분리한다.

## Architecture / Workflow Review
- 기존 task runtime과 incident runtime을 함수/모듈 경계로 분리해 결합도를 낮춘다.
- Stage 8 상세설계의 흐름(ingest -> rag -> action -> gate -> report)을 main에 명시적으로 반영한다.
- action gate는 정책/승인 판단 전용으로 유지하고 adapter에서 정책결정을 하지 않는다.
- 실패복구는 기존 `MAX_RETRY` 정책을 우선 재사용한다.

## QA Gate Review
- Plan/Review 단계 통과 후 구현 착수:
  - `bash scripts/run_micro_cycle.sh gate-plan stage8-w3-001`
  - `bash scripts/run_micro_cycle.sh gate-review stage8-w3-001`
- 구현 후 필수 검증:
  - `python3 -m unittest tests.test_incident_runtime_smoke`
  - `bash scripts/run_micro_cycle.sh run stage8-w3-001 8`
  - `bash scripts/run_stage8_self_eval.sh`

## Review Verdict
- 조건부 승인 (Approved with Guardrails)
- 조건:
  1. 기존 task 엔드포인트 계약 회귀를 허용하지 않는다.
  2. 정책/승인 우회 경로가 발견되면 즉시 반려한다.
  3. 구현 완료 시 G2 그룹 상태를 `PASS`로 갱신한다.
