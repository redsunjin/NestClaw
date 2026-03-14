# Sync Notes

## Release Actions
- feature worktree에서 `feat(agent): expose planner provenance in ui` 커밋(`1500bc3`)을 push했다.
- QA worktree를 `git merge --ff-only 1500bc3`으로 fast-forward 했다.
- QA canonical cycle을 fresh SQLite 경로로 재실행해 planner provenance UI surface와 recent payload 확장을 다시 검증했다.

## QA Sync Evidence
- feature evaluate gate:
  - `work/micro_units/stage8-w5-028/reports/evaluate-gate-20260314T173641Z.md`
- feature dev QA cycle:
  - `reports/qa/cycle-20260314T173641Z.md`
- QA canonical cycle:
  - `reports/qa/cycle-20260314T173712Z.md`
- QA grouped self-eval:
  - `reports/qa/stage8-self-eval-20260314T173726Z.md`
- QA runtime smoke에서 web console runtime, agent entrypoint runtime, stage8 facade/runtime smoke가 모두 PASS였다.

## Final State
- quickstart와 console 모두 current task의 planner source/provider/tool flow를 직접 보여준다.
- recent task payload와 recent card도 planner provenance 요약을 노출해 operator가 현재 AI planner 상태를 더 쉽게 이해할 수 있다.
- priority campaign의 다음 대상은 `stage8-w5-029`, 즉 tool governance hardening이다.
