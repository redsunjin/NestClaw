# Review Notes

## Security / Policy Review
- Agent Profile은 persona 정의가 아니라 provider/job/capability boundary여야 한다.
- local LLM은 sensitive/internal 작업의 기본 경로로 두고, cloud/API provider는 explicit policy와 sensitivity boundary가 있을 때만 허용해야 한다.
- profile에는 execution budget과 approval policy가 반드시 포함되어야 한다.
- unrestricted filesystem/tool access를 허용하는 profile은 금지해야 한다.

## Architecture / Workflow Review
- Stage 12 하네스는 새 runtime 구현보다 먼저 static contract를 잡는 것이 적절하다.
- `run_dev_qa_cycle.sh`와 `run_auto_cycle.sh`가 Stage 12를 공식 target으로 받아야 로드맵 drift를 막을 수 있다.
- 초기 `tests.test_stage12_contract`는 positioning, roadmap, campaign, MWU, capability manifest, provider guardrail을 검증하는 수준이면 충분하다.
- Agent Profile spec 구현 시에는 model registry와 capability manifest를 참조하되, 기존 planner/executor 루프를 우회하면 안 된다.

## QA Gate Review
- `python3 -m unittest tests.test_stage12_contract`가 Stage 12 문서와 campaign baseline을 검증해야 한다.
- `bash scripts/run_dev_qa_cycle.sh 12`가 Stage 1-12 전체 contract를 통과해야 한다.
- optional env-gated skip은 기존 Stage 8 blocker와 동일하게 유지하되, Stage 12 contract failure와 섞지 않아야 한다.

## Review Verdict
- 진행 승인.
- 이번 하네스 보강은 Stage 12 static contract와 cycle target 확장으로 제한하고, runtime agent profile validator는 G1 implement 범위에서 다룬다.
