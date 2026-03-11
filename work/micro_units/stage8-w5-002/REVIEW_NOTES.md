# Review Notes

## Security / Policy Review
- 단일 agent 진입점도 기존 RBAC/approval/policy를 우회하면 안 된다.
- 라우팅 결과가 incident일 경우 기존 policy gate와 approval queue를 그대로 사용해야 한다.
- agent 입력 원문은 실행 payload와 분리해 기록하고, 민감정보 마스킹 규칙은 기존 adapter에 맡긴다.
- 잘못된 라우팅이 고위험 incident live 실행으로 이어지지 않도록 incident 기본 run mode는 계속 dry-run이어야 한다.

## Architecture / Workflow Review
- 현재 구조의 핵심 문제는 `task API`, `incident API`, `CLI`가 서로 다른 진입점으로 노출된 점이다.
- 제품 관점 1순위는 엔진 추가가 아니라 사용자 계약 통합이다.
- 따라서 이번 단위는 새 에이전트 엔진을 만드는 것이 아니라 기존 workflow를 감싸는 `facade`를 만드는 작업으로 제한한다.
- 라우팅은 규칙 기반으로 시작하고, 이후 실제 LLM 연결 시 교체 가능한 helper 함수로 분리한다.

## QA Gate Review
- 필수 검증:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `python3 -m unittest tests.test_agent_entrypoint_smoke`
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-002 8`
- QA worktree에서는 `.venv`로 runtime smoke와 agent smoke를 실제 실행한다.

## Review Verdict
- 조건부 승인 (Approved as Facade First)
- 조건:
  1. 기존 `/task/*`와 `/incident/*`를 깨지 않아야 한다.
  2. 단일 진입점은 workflow type을 감추되 내부 정책/승인 로직은 그대로 재사용해야 한다.
  3. intent classification은 rule-based 한계를 문서에 명시해야 한다.
