# Git Worktree Guide

## 왜 쓰는가
- 한 저장소에서 여러 브랜치를 동시에 작업할 수 있다.
- 예: `main`은 안정 상태로 유지, `codex/feature-a`는 별도 폴더에서 병렬 개발.
- 브랜치 전환 충돌(`stash`, 미커밋 변경 충돌)을 줄인다.

## 기본 개념
- 원본 저장소(`new_claw/.git`)를 공유한다.
- 작업 디렉터리만 여러 개 만든다.
- 각 worktree는 서로 다른 브랜치를 체크아웃한다.

## 추천 디렉터리 구조
- 기준 저장소: `new_claw` (main)
- 병렬 작업용:
  - `../new_claw-wt-feature-a`
  - `../new_claw-wt-qa`

## 실전 명령
1. 현재 worktree 목록:
```bash
git worktree list
```

2. 새 브랜치를 새 worktree로 생성:
```bash
git worktree add -b codex/feature-a ../new_claw-wt-feature-a main
```

3. 기존 브랜치를 worktree로 체크아웃:
```bash
git worktree add ../new_claw-wt-qa codex/test-flow
```

4. worktree 제거:
```bash
git worktree remove ../new_claw-wt-feature-a
```

5. 정리:
```bash
git worktree prune
```

## 운영 규칙 (이 프로젝트 권장)
- `main` worktree:
  - 배포/기준 문서 확인 전용
- feature worktree:
  - `codex/<topic>` 단위 구현
- QA worktree:
  - `scripts/run_dev_qa_cycle.sh` 및 테스트 반복

## 주의
- 같은 브랜치를 2개 worktree에서 동시에 checkout할 수 없다.
- worktree 디렉터리를 OS에서 강제로 지우지 말고 `git worktree remove` 사용.
- 공용 `.git`를 공유하므로 커밋/브랜치/태그는 저장소 전체에 반영된다.
