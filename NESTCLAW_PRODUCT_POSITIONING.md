# NestClaw Product Positioning

## 1. Canonical Definition
- NestClaw는 로컬 LLM과 상위 cloud/API LLM이 조직 내부 작업을 정책·승인·감사와 함께 실행하도록 관리하는 closed orchestration runtime이다.
- NestClaw의 1차 제품 정체성은 `local-first LLM job control plane`이다.
- NestClaw의 2차 제품 정체성은 `agent-facing integration layer + human approval/audit dashboard`다.
- 조직 환경에서는 이를 `조직용 orchestration control plane`으로 배치한다.

## 2. What NestClaw Is
- 자연어 목표를 받아 `task` 또는 `incident` workflow로 라우팅하는 orchestration backend
- planner, executor, reviewer, reporter, approval, audit를 한 runtime contract로 묶는 control plane
- HTTP, MCP, non-interactive CLI를 통해 상위 agent와 스크립트가 호출하는 하위 실행 계층
- 인간 운영자가 승인, 감사, blocked reason, readiness를 확인하는 operator dashboard
- 로컬 LLM이 승인된 job template과 capability pack 안에서만 작업을 수행하도록 제한하는 작업 실행 관리자
- cloud/API LLM을 조직 정책과 sensitivity routing 안에서 선택적으로 사용할 수 있는 provider-managed runtime

## 3. What NestClaw Is Not
- agent marketplace
- 사람용 메인 채팅 업무 앱
- 별도 human interactive TUI 제품
- 개별 agent들의 모음집
- policy와 approval을 우회하는 실행 허브
- unrestricted local LLM agent runner
- cloud/API LLM 의존형 SaaS agent hub

## 4. Primary Users
- 상위 대화형 에이전트
- 로컬 LLM wrapper / local agent runner
- 운영 자동화 스크립트
- approver / admin / reviewer

## 5. Primary Surfaces
- HTTP API
- MCP
- non-interactive CLI
- operator dashboard(`/console`)

## 6. Non-Goals
- 사람용 독립 TUI 확대
- catalog를 공개형 plugin/agent marketplace처럼 확장
- dashboard chat을 주 실행 인터페이스로 승격
- 여러 persona agent를 제품 전면 개념으로 내세우는 것

## 7. Language Guide
### Prefer
- `local-first LLM job control plane`
- `로컬 LLM용 안전한 작업 실행 관리자`
- `조직용 orchestration runtime`
- `orchestration control plane`
- `상위 에이전트가 호출하는 backend`
- `human approval/audit dashboard`
- `curated capability registry`

### Avoid
- `에이전트 모음`
- `멀티 에이전트 허브`
- `AI 서비스 허브 앱`
- `사람용 메인 채팅 앱`
- `marketplace`
- `무제한 로컬 에이전트 런처`

## 8. Product Consequence
- 로드맵 우선순위는 surface 확장보다 contract, approval, audit, capability control이 된다.
- GUI 우선순위는 상태/승인/감사/해석이다.
- 상위 agent와 NestClaw는 경쟁 관계가 아니라 계층 관계다.
- 로컬 LLM은 기본 실행 경로지만, cloud/API LLM은 정책이 허용하는 작업에서 선택 가능한 provider로 유지한다.
- 다음 제품 확장은 `agent profile`, `job template`, `capability pack`, `execution budget`, `schedule trigger`를 중심으로 판단한다.
