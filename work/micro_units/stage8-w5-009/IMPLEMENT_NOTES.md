# Implement Notes

## Changed Files
- [x] `README.md`
  - 제품 목적을 `다양한 도구를 사용하는 업무 실행 에이전트`로 재정의하고 현재 구현 범위(`task`, `incident`)를 분리해 설명
- [x] `IDEATION_ONEPAGER.md`
  - 상위 제품 정의와 Stage 8의 `첫 번째 high-risk vertical` 위치를 고정
- [x] `AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md`
  - tool registry / capability schema 필요성과 다음 MWU 후보를 broader execution agent 기준으로 재정렬
- [x] `INCIDENT_ORCHESTRATION_RAG_MCP_PLAN.md`
  - incident 자동화를 제품 전체 목표가 아니라 첫 번째 vertical 설계 문서로 재라벨링
- [x] `STAGE8_CLOSEOUT_SUMMARY_2026-03-06.md`
  - Stage 8 결과를 broader execution agent의 vertical 증적으로 위치 조정
- [x] `TASKS.md`
  - Stage 8 헤더를 `첫 번째 vertical`로 수정하고 tool registry / tool planning follow-up 추가
- [x] `NEXT_STAGE_PLAN_2026-02-24.md`
  - 제품 정의, 진단, 다음 우선순위를 `도구 실행형 에이전트` 기준으로 갱신
- [x] `API_CONTRACT.md`
  - 현재 v0.1 workflow family 범위와 `task_kind=auto`의 현재 동작을 명시
- [x] `tests/test_stage8_contract.py`
  - 제품 정의 / vertical 위치 / API 범위 정렬 회귀 테스트 추가
- [x] `work/micro_units/stage8-w5-009/*`
  - plan/review/implement/evaluate 자산 생성

## Rollback Plan
- 전체 롤백: `git revert <this-commit>`
- 부분 롤백 대상:
  - `README.md`
  - `IDEATION_ONEPAGER.md`
  - `AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md`
  - `INCIDENT_ORCHESTRATION_RAG_MCP_PLAN.md`
  - `STAGE8_CLOSEOUT_SUMMARY_2026-03-06.md`
  - `TASKS.md`
  - `NEXT_STAGE_PLAN_2026-02-24.md`
  - `API_CONTRACT.md`
  - `tests/test_stage8_contract.py`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_spec_contract tests.test_stage8_contract`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-009 8`

## Known Risks
- Stage 8 historical 문서를 broader product 방향에 맞게 재라벨링했으므로, 당시 의사결정 배경을 모르면 현재 방향과 혼동될 수 있다.
- `도구 실행형 에이전트`라는 상위 정의는 맞지만, 실제 구현 범위는 여전히 `task/incident` 두 family에 제한된다.
- tool registry / tool planner 구현 전까지는 문서 비전이 코드 능력을 앞설 수 있다.
