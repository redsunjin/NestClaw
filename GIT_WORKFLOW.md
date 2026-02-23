# Git Workflow for `new_claw`

## 1) Branch Strategy
- Default branch: `main`
- Working branch pattern: `codex/<topic>`
- Rule: do not work directly on `main`

## 2) Commit Convention
- Format: `<type>(<scope>): <summary>`
- Allowed types:
  - `feat`
  - `fix`
  - `docs`
  - `chore`
  - `refactor`
  - `test`

Example:
```text
feat(api): add task create run status endpoints
```

## 3) Pull Request Rule
- Use same title style as commit convention
- PR body must include:
  - Change summary
  - Test result
  - Risk / rollback notes

Template file:
- `.github/pull_request_template.md`

## 4) Release Tag Rule
- Semantic version tag: `vMAJOR.MINOR.PATCH`
- First release baseline: `v0.1.0`

## 5) Safety Rules
- Never use `git reset --hard` in normal workflow
- Prefer `git revert` for undo
- Keep `main` deployable/stable

## 6) Daily Flow
1. Create work branch:
```bash
git checkout -b codex/<short-topic>
```
2. Commit:
```bash
git add -A
git commit -m "feat(<scope>): <summary>"
```
3. Push branch:
```bash
git push -u origin codex/<short-topic>
```
4. Create PR and merge to `main`
5. Sync local `main`:
```bash
git checkout main
git pull --ff-only
```

