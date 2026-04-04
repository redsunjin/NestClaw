# Review Notes

## Security / Policy Review
- provider selection helper는 audit/observability 강화용이어야 하며, approval policy를 직접 바꾸거나 우회하면 안 된다.
- report/result finalization helper는 `DONE` 판정과 report path 기록을 단순화하되, 완료 이전에 결과를 추정해 확정하는 경로를 만들면 안 된다.
- requester/approver/admin 역할 경계는 이번 단위와 무관하게 유지되어야 하며, helper 추출이 role semantics를 바꾸면 안 된다.

## Architecture / Workflow Review
- 이번 단위는 `planner_executor_service`에 후반부 rail을 추가하는 방식이 적절하다.
- task/incident가 공통 helper를 쓰더라도 workflow-specific report 내용과 compatibility field(`action_cards`)는 유지해야 한다.
- `_record_provider_selection`, `_write_report`, 완료 result 마감이 공통 helper로 옮겨지면 `app/main.py`의 workflow별 duplication을 줄일 수 있다.

## QA Gate Review
- `tests.test_stage9_contract`는 stage9 campaign과 두 번째 G1 MWU가 문서상 고정됐는지 확인해야 한다.
- `tests.test_planner_executor_service`는 fastapi 없이도 helper contract를 검증해야 한다.
- runtime smoke는 task/incident의 `provider_selection`, `action_results`, `result.report_path`, `completed_at`이 그대로 유지되는지 봐야 한다.
- 최종 gate는 `env PATH="../nestclaw-ideation-qa/.venv/bin:$PATH" bash scripts/run_dev_qa_cycle.sh 9`다.

## Review Verdict
- 진행 승인.
- 이번 단위는 G1 후속 정리 범위로 타당하며, incident AI planner 확장과 UI 변경은 다음 단위로 미룬다.
