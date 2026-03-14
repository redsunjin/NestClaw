# Sync Notes

## Release Actions
- feature worktree에서 `feat(agent): add campaign workflow and incident planner provenance` 커밋(`a742d47`)을 push했다.
- QA worktree를 `git merge --ff-only a742d47`으로 fast-forward 했다.
- QA canonical cycle을 fresh SQLite 경로로 재실행해 incident planner provenance path와 campaign workflow assets를 다시 검증했다.

## QA Sync Evidence
- feature evaluate gate:
  - `work/micro_units/stage8-w5-026/reports/evaluate-gate-20260314T172438Z.md`
- feature wrapper status:
  - `work/micro_units/stage8-w5-026/reports/expert-agent-status-20260314T172622Z.md`
- QA canonical cycle:
  - `reports/qa/cycle-20260314T172528Z.md`
- QA grouped self-eval:
  - `reports/qa/stage8-self-eval-20260314T172542Z.md`
- QA runtime smoke는 canonical cycle에서 `stage8 incident runtime smoke tests` PASS로 확인했다.

## Final State
- `stage8-w5-026`는 incident path에도 `planning_provenance`와 `INCIDENT_PLAN_GENERATED`를 추가해 task/incident 공통 planner-executor 관측 계약을 맞췄다.
- priority campaign 레이어는 실제로 `stage8-priority-campaign`에 적용되어 다음 item advance 준비가 끝난 상태다.
- 다음 1순위는 `stage8-w5-027`, 즉 cross-action data binding과 richer sequencing이다.
