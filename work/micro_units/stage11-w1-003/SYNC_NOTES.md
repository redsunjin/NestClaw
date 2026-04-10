# Sync Notes

## Release Actions
- `NESTCLAW_DEPLOYMENT_BOOTSTRAP_PROFILES_2026-04-08.md`를 추가해 local dev / operator sidecar / upper-agent host가 같은 bootstrap contract를 읽도록 정리했다.
- `configs/deployment_bootstrap_profiles.json`에 machine-readable canonical profile을 추가했고, `scripts/validate_deployment_bootstrap_profiles.sh`로 schema drift를 빠르게 검증할 수 있게 했다.
- `NESTCLAW_MCP_TRANSPORT_DEPLOYMENT_GUIDE.md`와 `README.md`를 새 bootstrap guide/artifact를 참조하도록 갱신해 사람이 보는 운영 문서와 machine-readable profile이 분리되지 않게 맞췄다.
- `scripts/run_dev_qa_cycle.sh`, `tests/test_stage11_contract.py`, `tests/test_stage11_deployment_bootstrap_smoke.py`를 통해 Stage 11 cycle이 bootstrap profile baseline을 계속 회귀 검증하게 했다.

## QA Sync Evidence
- `work/micro_units/stage11-w1-003/reports/plan-gate-20260406T151745Z.md`
- `work/micro_units/stage11-w1-003/reports/review-gate-20260408T130739Z.md`
- `work/micro_units/stage11-w1-003/reports/implement-gate-20260408T130926Z.md`
- `work/micro_units/stage11-w1-003/reports/evaluate-gate-20260408T131145Z.md`
- `reports/qa/cycle-20260408T130931Z.md`
- `bash scripts/validate_deployment_bootstrap_profiles.sh`
- `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" python3 -m unittest tests.test_stage11_contract tests.test_stage11_deployment_bootstrap_smoke`

## Final State
- `stage11-w1-003`은 조직 내 반복 배치를 위한 deployment bootstrap profile baseline을 고정했고, operator와 upper-agent가 같은 startup/readiness language를 공유할 수 있게 됐다.
- transport guide, bootstrap guide, JSON profile, validator, Stage 11 QA cycle이 서로 연결되면서 launch profile drift를 조기에 잡는 구조가 생겼다.
- 다음 item은 `g4-pilot-acceptance-cycle`이다.
