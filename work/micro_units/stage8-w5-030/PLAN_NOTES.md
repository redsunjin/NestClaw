# Plan Notes

## Scope
- sandbox/live/self-eval을 묶어 한 번에 readiness evidence를 수집하는 bundle script를 추가한다.
- env가 없으면 missing env checklist와 blocked reason을 명시적으로 남기는 report를 생성한다.
- 최신 G4 상태와 실행 절차를 문서화해 외부 sandbox/live 준비가 끝나면 바로 재실행할 수 있게 만든다.
- 현재 환경에서 bundle을 실제 실행해 Stage 8 live-readiness blocker를 최신 보고서로 고정한다.

## Out of Scope
- 실제 Redmine sandbox credential 발급
- 외부 live endpoint 생성
- sandbox/live 자체의 외부 운영 승인 절차
- G1/G2/G3 추가 기능 개발

## AI-First Planner Design
- G4는 planner 기능 추가가 아니라 AI-first runtime을 운영환경까지 밀어 넣기 위한 readiness control plane이다.
- readiness bundle은 planner runtime과 별개지만, AI-first agent가 live tool surface를 사용할 수 있는지 자동으로 판정하는 운영 증적 계층이다.
- env가 비어 있으면 heuristic하게 숨기지 말고 blocked 상태를 명시해야 한다.
- self-eval, sandbox rehearsal, live rehearsal 결과를 한 보고서에 모아 다음 실행자가 바로 판단할 수 있게 해야 한다.

## Acceptance Criteria
- readiness bundle script가 존재하고 sandbox/live/self-eval 결과를 하나의 report로 묶는다.
- env 누락 시 missing env 목록과 blocked reason이 report에 기록된다.
- 최신 runtime readiness guide가 존재하고 필요한 env/명령이 정리된다.
- 현재 환경에서 readiness bundle을 실행한 증적 report가 생성된다.
- stage 8 micro-cycle과 QA canonical cycle이 통과한다.

## Risks
- blocked를 PASS처럼 보이게 기록하면 readiness 판단을 왜곡할 수 있다.
- readiness bundle이 기존 rehearsal script와 다른 판정 규칙을 쓰면 운영자가 혼동할 수 있다.
- env checklist가 최신 live/sandbox 요구사항과 어긋나면 잘못된 준비를 유도할 수 있다.

## Test Plan
- `bash scripts/run_micro_cycle.sh gate-plan stage8-w5-030`
- `bash scripts/run_micro_cycle.sh gate-review stage8-w5-030`
- `bash scripts/run_stage8_readiness_bundle.sh`
- `python3 -m unittest tests.test_stage8_contract`
- `bash scripts/run_micro_cycle.sh run stage8-w5-030 8`
