# Implement Notes

## Changed Files
- `app/services/orchestration_service.py`
- `app/main.py`
- `app/cli.py`
- `app/mcp_server.py`
- `app/services/capability_manifest_service.py`
- `NESTCLAW_OPERATOR_HANDOFF_PACKET_SPEC.md`
- `NESTCLAW_AGENT_INTEGRATION_SPEC.md`
- `NESTCLAW_INTEGRATION_EXAMPLES.md`
- `NESTCLAW_CAPABILITY_MANIFEST.md`
- `README.md`
- `tests/test_agent_entrypoint_smoke.py`
- `tests/test_tool_cli_smoke.py`
- `tests/test_mcp_server_smoke.py`
- `tests/test_capability_manifest_runtime.py`
- `tests/test_stage11_contract.py`
- `work/micro_units/stage11-w1-002/REVIEW_NOTES.md`

## Rollback Plan
- handoff packet은 additive export surface라, 문제가 생기면 `agent.handoff` route/tool/command와 related doc/test만 제거하면 기존 `agent.bundle` 중심 observe loop로 즉시 되돌릴 수 있다.
- capability manifest의 `safe_for_upper_agents`에 handoff를 추가한 것도 additive라, 필요 시 해당 control entry만 제거해 상위 agent 표면을 이전 상태로 복귀시킬 수 있다.
- markdown rendering이 예상보다 noisy하면 structured JSON packet은 유지한 채 CLI plain renderer와 markdown field만 축소하는 부분 롤백도 가능하다.

## Known Risks
- handoff packet이 bundle과 다른 vocabulary를 쓰기 시작하면 operator/upper-agent 간 drift가 생기므로 state/reason naming은 runtime taxonomy에 계속 종속돼야 한다.
- requester/reviewer에게도 markdown packet이 보이기 때문에 approval detail gating이 깨지지 않도록 summary/detail boundary를 계속 주의해야 한다.
- packet_type `blocked`는 현재 `retryable_failure`와 env-like blocked semantics를 같이 묶는 operator view이므로, 이후 richer blocked class가 생기면 분류를 더 세분화해야 할 수 있다.
