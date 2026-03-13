# Implement Notes

## Changed Files
- 제품 정의/아키텍처/우선순위 재정렬:
  - `README.md`
  - `IDEATION_ONEPAGER.md`
  - `AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md`
  - `NEXT_WORK_GROUPS_2026-03-13.md`
  - `NEXT_STAGE_PLAN_2026-02-24.md`
  - `TASKS.md`
  - `API_CONTRACT.md`
  - `AGENT_EXPERT_GROUP.md`
- 전문가 운영 프로토콜 보강:
  - `EXPERT_AGENT_OPERATING_PROTOCOL_2026-03-13.md`
  - `scripts/run_expert_agent_workflow.sh`
  - `scripts/run_micro_cycle.sh`
  - `templates/MICRO_WORK_UNIT_TEMPLATE.md`
- 회귀 방지 계약 테스트:
  - `tests/test_stage8_contract.py`

## Rollback Plan
- 이번 변경은 문서/프로토콜/계약 테스트 중심이므로, 문제가 생기면 해당 문서와 테스트 기대값을 직전 커밋으로 되돌리면 된다.
- runtime code path는 직접 변경하지 않았으므로 서비스 동작 회귀 시 문서 변경보다 테스트 기대값 불일치 여부를 먼저 확인한다.

## Known Risks
- A03를 별도 top-level gate로 분리하지는 않았고, `Plan` 패키지 안의 필수 설계 검토로 반영했다.
- 따라서 자동화는 강화됐지만, 완전한 별도 planner gate가 필요하면 후속 MWU에서 추가 확장이 필요하다.
