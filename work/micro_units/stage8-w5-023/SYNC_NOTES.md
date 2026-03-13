# Sync Notes

## Release Actions
- feature worktree에서 AI-first 정렬 변경을 커밋하고 push한다.
- QA worktree를 fast-forward 한다.

## QA Sync Evidence
- QA canonical cycle report 경로를 기록한다.
- 필요 시 `bash scripts/run_expert_agent_workflow.sh status stage8-w5-023 8` 출력과 clean worktree 상태를 기록한다.

## Final State
- `stage8-w5-023`가 `COMPLETED`가 되도록 sync evidence를 남기고 wrapper `sync` 명령으로 마감한다.
