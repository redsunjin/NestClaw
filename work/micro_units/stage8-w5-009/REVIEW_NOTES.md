# Review Notes

## Security / Policy Review
- 제품 정의가 넓어져도 승인/정책/감사 원칙이 약해지면 안 된다.
- 문서에 `다양한 도구`를 적더라도 무제한 자동 실행이 아니라 allowlist/approval 기반임을 유지해야 한다.
- incident vertical을 첫 번째 use case로 낮추더라도 high-risk workflow라는 점은 유지해야 한다.

## Architecture / Workflow Review
- 현재 제품은 `agent facade + task/incident workflow family + CLI/MCP/API` 수준이다.
- 따라서 문서는 `broad product definition`과 `current implemented workflows`를 분리해서 써야 한다.
- Stage 8 문서는 historical/vertical 문서이므로 삭제보다 재라벨링이 맞다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-009 8`
- 정적 계약 테스트에 제품 정의/vertical 정렬 문구를 추가해 회귀를 막는다.

## Review Verdict
- 승인 (Approved as Documentation Alignment)
- 조건:
  1. 제품 정의와 현재 구현 범위를 같은 문단에서 혼동하지 말 것
  2. incident Stage 8은 broader execution agent의 `첫 번째 vertical`로 표현할 것
  3. `다양한 도구`는 반드시 정책/승인/감사 전제와 함께 적을 것
