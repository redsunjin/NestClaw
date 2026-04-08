# Plan Notes

## Scope
- local dev, sidecar operator, upper-agent host가 공통으로 참고할 deployment bootstrap profile을 문서 또는 설정 템플릿으로 고정한다.
- 최소한 `uvicorn app.main:APP`와 `python3 app/mcp_server.py`를 어떤 actor/auth/readiness 절차로 띄울지 profile별로 정리한다.
- auth mode별 startup hint, health check, restart 기준, readiness preflight를 한 군데에서 읽히게 만든다.
- 가능하면 launch profile example 또는 shell/bootstrap artifact를 추가하고, Stage 10의 MCP transport guide와 충돌하지 않게 연결한다.

## Out of Scope
- 실제 remote gateway 구현
- container/orchestrator 배포 자동화
- secret manager 통합
- live external env 발급
- dashboard chat panel 또는 planner logic 변경

## AI-First Planner Design
- 이번 단계는 새 agent intelligence를 추가하는 작업이 아니라, upper agent와 operator가 같은 bootstrap contract로 runtime을 띄우게 만드는 operationalization 단계다.
- 이미 MCP transport baseline은 stdio로 정리돼 있으므로, 이번 단계는 `어떻게 붙을까`보다 `어떻게 반복 가능하게 띄울까`를 고정하는 데 집중하는 편이 맞다.
- deployment profile은 새 control surface가 아니라 기존 HTTP + MCP + auth mode를 반복 가능한 profile로 패키징해야 하며, local dev와 operator sidecar의 차이만 최소한으로 드러나게 하는 구조가 적절하다.
- 따라서 문서, example launch profile, readiness/health 기준이 같은 vocabulary를 쓰도록 만드는 것이 핵심이다.

## Acceptance Criteria
- canonical deployment/bootstrap profile 문서 또는 동등한 artifact가 존재한다.
- local dev / sidecar operator / upper-agent host 최소 3개 profile의 startup command와 health/readiness 절차가 정리된다.
- auth mode와 actor context boundary가 profile 문서 안에서 빠지지 않고 설명된다.
- 관련 contract/test와 `bash scripts/run_dev_qa_cycle.sh 11`이 통과한다.
- operator가 새 profile 문서만 보고 uvicorn + MCP stdio baseline을 재현할 수 있다.

## Risks
- bootstrap profile이 현재 실제 startup flags나 auth mode와 어긋나면 operator가 거짓 기준으로 배치하게 된다.
- local dev와 sidecar operator profile 차이를 과하게 숨기면 trust boundary나 actor injection 책임이 흐려질 수 있다.
- deployment guide가 transport guide와 중복되기만 하고 launch/restart readiness 관점이 추가되지 않으면 가치가 떨어진다.
- shell/bootstrap artifact를 추가할 경우 환경 의존 경로가 과하게 하드코딩되면 재사용성이 낮아질 수 있다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage11-w1-003`
- `bash scripts/run_micro_cycle.sh gate-review stage11-w1-003`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_stage11_contract`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 11`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_micro_cycle.sh run stage11-w1-003 11`
