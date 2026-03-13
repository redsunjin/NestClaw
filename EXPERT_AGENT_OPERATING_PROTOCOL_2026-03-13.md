# Expert Agent Operating Protocol (2026-03-13)

## 목적
NestClaw의 구현 작업을 사람이 임의로 밀어붙이는 방식이 아니라, `전문가 에이전트 역할 분리 + 게이트 강제 + 결과 동기화` 절차로 일관되게 수행한다.

이 문서는 기존 [MICRO_AGENT_WORKFLOW.md](/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation/MICRO_AGENT_WORKFLOW.md)를 대체하지 않는다.  
`MICRO_AGENT_WORKFLOW`가 MWU 게이트 표준이라면, 이 문서는 `누가 어떤 순서로 움직이고 어떤 자동화 명령으로 절차를 강제하는지`를 선언한다.

## 선언
- 모든 제품/플랫폼 구현은 Micro Work Unit(MWU) 단위로 자른다.
- 각 MWU는 `Plan -> Review -> Implement -> Evaluate -> Sync` 순서로만 진행한다.
- 각 단계는 다른 전문 에이전트가 책임진다.
- 자동화는 기존 `scripts/run_micro_cycle.sh`를 게이트 엔진으로 사용하고, 상위 오케스트레이션은 `scripts/run_expert_agent_workflow.sh`가 맡는다.
- `Sync`는 QA worktree 동기화와 evidence 기록이 끝난 뒤 wrapper의 `sync` 명령으로 완료 처리한다.
- feature worktree에서 구현하고, QA worktree에서 canonical 검증한다.

## 전문가 에이전트 역할
| 단계 | 담당 에이전트 | 책임 |
|---|---|---|
| Plan | A01 Product Planner | 범위, 비범위, acceptance, risk, test plan 고정 |
| Review | A04 Security Reviewer | 권한/정책/구조/QA 관점 검토 |
| Implement | A02 Workflow Engineer | 코드/문서/테스트 구현 |
| Evaluate | A06 QA Reliability | micro-cycle, canonical QA, 실제 smoke 검증 |
| Sync | A09 Release Sync | commit, push, QA worktree fast-forward, evidence 정리 |

## 표준 절차
1. `A01`이 MWU를 선언한다.
2. `A04`가 구현 전 검토를 끝낸다.
3. `A02`가 구현 후 implement notes를 채운다.
4. `A06`가 `run_micro_cycle`과 QA worktree 검증으로 evaluate를 닫는다.
5. `A09`가 commit/push/QA sync/evidence 반영까지 마무리한다.

## 자동화 규칙
- MWU 생성/게이트는 `scripts/run_micro_cycle.sh`가 단일 진실 원천이다.
- 다음 담당 단계 판정과 verify 실행은 `scripts/run_expert_agent_workflow.sh`가 수행한다.
- wrapper는 노트 내용을 자동 작성하지 않는다.
  - 대신 현재 단계, 다음 담당 에이전트, 추천 명령을 고정해서 절차 이탈을 막는다.
- `Evaluate` 이후에는 반드시 QA worktree canonical cycle과 실제 서버 확인을 수행한다.

## 자동 실행 진입점
```bash
# MWU 준비
bash scripts/run_expert_agent_workflow.sh prepare <unit_id> "<goal>" 8

# 현재 단계/다음 담당자 확인
bash scripts/run_expert_agent_workflow.sh status <unit_id> 8

# gate verify
bash scripts/run_expert_agent_workflow.sh verify <unit_id> 8

# sync 완료 마감
bash scripts/run_expert_agent_workflow.sh sync <unit_id> 8
```

## 다음 담당자 판정 규칙
- Plan gate 미완료: `A01 Product Planner`
- Review gate 미완료: `A04 Security Reviewer`
- Implement gate 미완료: `A02 Workflow Engineer`
- Evaluate gate 미완료: `A06 QA Reliability`
- Sync evidence 미완료: `A09 Release Sync`
- Sync까지 완료: `COMPLETED`

## worktree 운영 규칙
- feature worktree: 구현, 문서화, feature micro-cycle
- QA worktree: canonical QA, browser smoke, 실제 수동 확인
- QA 중 생성된 runtime overlay/test artifact는 검증 후 정리해 clean 상태를 유지한다.

## 제품 화면과의 연결
- root(`/`)는 사용자용 단일 진입 화면이다.
- advanced console(`/console`)은 운영/디버그용이다.
- 즉, 사용자 흐름은 단순화하고 내부 작업 절차는 더 엄격하게 유지한다.
