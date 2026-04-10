# Implement Notes

## Changed Files
- `NESTCLAW_DEPLOYMENT_BOOTSTRAP_PROFILES_2026-04-08.md`
- `configs/deployment_bootstrap_profiles.json`
- `scripts/validate_deployment_bootstrap_profiles.sh`
- `NESTCLAW_MCP_TRANSPORT_DEPLOYMENT_GUIDE.md`
- `README.md`
- `scripts/run_dev_qa_cycle.sh`
- `tests/test_stage11_contract.py`
- `tests/test_stage11_deployment_bootstrap_smoke.py`
- `work/micro_units/stage11-w1-003/REVIEW_NOTES.md`

## Rollback Plan
- bootstrap profile은 additive guide/artifact이므로, 문제가 생기면 새 guide/profile/validator와 Stage 11 smoke만 제거하고 기존 MCP transport guide 기준으로 되돌릴 수 있다.
- `run_dev_qa_cycle.sh`에 추가한 stage11 deployment smoke도 한 줄 추가 수준이라, 필요 시 해당 check만 제거하면 기존 cycle 구조에 영향 없이 복귀한다.
- operator/upper-agent가 이미 transport guide를 쓰고 있었다면, 새 profile artifact를 무시하고 기존 명령만 유지하는 soft rollback도 가능하다.

## Known Risks
- bootstrap profile JSON이 실제 운영 명령보다 앞서 변하면 validator는 PASS인데 현장 절차가 틀릴 수 있으므로 guide와 artifact를 같이 갱신해야 한다.
- upper-agent host profile에서 HTTP를 optional로 둔 이유가 잘못 전달되면 “HTTP 불필요”로 과도하게 해석될 수 있어 observability 용도는 계속 문서에 남겨야 한다.
- auth mode를 예시 수준으로만 적었기 때문에 조직별 ingress/SSO wrapper 세부 구현은 여전히 별도 운영 문서가 필요하다.
