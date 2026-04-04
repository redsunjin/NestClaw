# oh-my-openagent v3.11.0 Adoption Review (2026-03-25)

## 목적
- `oh-my-openagent v3.11.0`에서 닫힌 조직/동아리/소규모 팀용 NestClaw에 실제로 가져올 만한 기능을 추린다.
- 단순 기능 나열이 아니라 서비스 확장 범위, 운영 부담, 성능 영향까지 함께 판단한다.

## 참고 소스
- release: [oh-my-openagent v3.11.0](https://github.com/code-yeongyu/oh-my-openagent/releases/tag/v3.11.0)
- 현재 제품 상태:
  - [README.md](/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation/README.md)
  - [AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md](/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation/AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md)
  - [NEXT_WORK_GROUPS_2026-03-17.md](/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation/NEXT_WORK_GROUPS_2026-03-17.md)

## 현재 전제
- NestClaw는 `task AI-first baseline + incident common contract` 단계다.
- `approval`, `tool registry`, `model registry`, `CLI/MCP/API`, `Quickstart/Console`, `priority campaign`은 이미 있다.
- 아직 부족한 것은 `incident AI planner`, `richer sequencing`, `operator action transparency`, `live readiness`다.
- 따라서 참고 프로젝트의 거대한 agent catalog 전체를 복제하는 것은 목표와 맞지 않는다.

## 가져올 만한 항목
### 1. QA Executability Preflight
- 참고 포인트:
  - manual QA execution and acceptance criteria workflow
  - QA scenario executability checks
- NestClaw 적용 방식:
  - planner 또는 preflight 단계에서 `qa_executable`, `missing_env`, `missing_role`, `missing_surface` 같은 판정을 남긴다.
  - `planning_provenance` 또는 별도 `execution_readiness` 필드에 기록한다.
  - Quickstart/Console에 실행 가능 여부를 바로 보여준다.
- 서비스 확장:
  - 작음
  - 주로 provenance/status/event/UI 확장
- 운영 영향:
  - 긍정적
  - env나 역할이 비어 있는 상태에서 헛실행하는 횟수를 줄인다.
- 성능 영향:
  - 거의 없음
- 판단:
  - `즉시 도입 추천`

### 2. Completion Verification Gate
- 참고 포인트:
  - Oracle verification mandatory
  - Final Verification Wave
- NestClaw 적용 방식:
  - `DONE` 직전에 lightweight verifier를 둔다.
  - verifier는 action result, approval state, report 생성 여부, 필수 artifact를 검사한다.
  - 결과를 `verification_summary` 또는 `completion_verification`으로 저장한다.
- 서비스 확장:
  - 작음 ~ 중간
  - task/incident 종료 경로, status/event, report summary에 영향
- 운영 영향:
  - 긍정적
  - 작은 조직에서 “끝났다”를 더 신뢰할 수 있게 된다.
- 성능 영향:
  - 작은 음수
  - task 종료 직전에 한 번 더 검사하므로 tail latency가 약간 늘어난다.
- 판단:
  - `우선 도입 추천`

### 3. Category-Based Model Routing / Fallback Cleanup
- 참고 포인트:
  - category defaults
  - model fallback cleanup
  - GPT-native routing 정리
- NestClaw 적용 방식:
  - 현재 model registry 위에서 `workflow kind`, `action family`, `reasoning effort` 기준 라우팅을 보강한다.
  - 죽은 fallback 또는 느린 체인을 줄인다.
  - planner/provider invocation에 fallback reason을 더 명시적으로 남긴다.
- 서비스 확장:
  - 작음 ~ 중간
  - model registry와 planner/provider selection 로직 위주
- 운영 영향:
  - 긍정적
  - 비용 예측과 디버깅이 쉬워진다.
- 성능 영향:
  - 보통 긍정적
  - 불필요한 fallback hop을 줄이면 지연 감소 가능
- 판단:
  - `도입 추천`

### 4. Internal Tool-Pack / Dispatch Profile
- 참고 포인트:
  - plugin dispatch
  - full agent catalog가 아니라 curated tool 묶음 운용
- NestClaw 적용 방식:
  - 공개 marketplace 대신 내부 preset pack만 지원한다.
  - 예:
    - `club-basic`
    - `ops-light`
    - `meeting-to-ticket`
    - `event-runbook`
  - pack은 tool registry overlay 조합 또는 allowlist profile로 관리한다.
- 서비스 확장:
  - 중간
  - registry overlay, governance, UI/CLI 선택면 필요
- 운영 영향:
  - 중간
  - pack 승인과 버전 관리 필요
- 성능 영향:
  - 거의 없음
- 판단:
  - `공개 marketplace는 비추천, 내부 preset pack 형태로만 추천`

### 5. Safe Parallel Tool-Calling Contract
- 참고 포인트:
  - parallel tool-calling behavioral contracts
- NestClaw 적용 방식:
  - tool capability에 `parallelizable`, `depends_on`, `barrier_after`, `exclusive_with` 같은 제약을 추가한다.
  - planner는 이를 읽어 실행 시퀀스를 만든다.
  - executor는 병렬 실행이 가능한 액션만 fan-out 한다.
- 서비스 확장:
  - 큼
  - planner, executor, event log, retry, UI 모두 영향
- 운영 영향:
  - 중간 ~ 높음
  - 실패면 디버깅이 더 어려워진다.
- 성능 영향:
  - 잠재적으로 큼
  - 제대로 맞으면 latency 감소, 잘못 맞으면 복잡도만 증가
- 판단:
  - `가치 높음, 하지만 Stage 9 G1/G2 이후 후순위`

## 보류 / 비추천 항목
### Full GPT-Native Agent Catalog Migration
- 비추천 이유:
  - 참고 프로젝트는 named agent ecosystem이 핵심이다.
  - NestClaw는 현재 `planner / executor / verifier` 최소 역할 구조가 더 적합하다.

### Public Marketplace Plugin Dispatch
- 비추천 이유:
  - 닫힌 조직/동아리용과 맞지 않는다.
  - 공개 plugin 유통보다 승인된 내부 pack이 맞다.

### auto_commit
- 보류 이유:
  - 서비스 기능으로서 가치가 낮다.
  - expert workflow 자동화 옵션으로는 가능하지만 제품 확장성과 직접 연결되지는 않는다.

### Automatic Image Conversion for HEIC/RAW/PSD
- 보류 이유:
  - 현재 NestClaw의 코어는 orchestration이다.
  - 실제 멀티모달 이미지 운영 업무 비중이 커지기 전까지는 우선순위가 낮다.

### Oracle-Style Session Tracking / Parent Retry
- 보류 이유:
  - 참고 프로젝트의 ULW-loop 구조에 강하게 묶여 있다.
  - NestClaw는 먼저 task/approval/rehearsal resume semantics를 단순화하는 편이 낫다.

## 적용 우선순위
1. QA Executability Preflight
2. Completion Verification Gate
3. Category-Based Model Routing / Fallback Cleanup
4. Internal Tool-Pack / Dispatch Profile
5. Safe Parallel Tool-Calling Contract

## 소규모 조직용 해석
- 동아리/작은 팀에서 중요한 것은 “더 많은 agent”가 아니라 아래 네 가지다.
- 실행 전에 검증 가능한지 알 수 있어야 한다.
- 끝났다고 말하기 전에 한 번 더 확인해야 한다.
- 필요한 tool 조합을 preset으로 단순화해야 한다.
- operator가 왜 이 action이 선택됐는지 바로 읽을 수 있어야 한다.

## 결론
- 참고 릴리즈에서 지금 바로 가져올 것은 `검증 강화`, `QA 실현가능성 체크`, `모델 라우팅 정리`다.
- 공개 plugin marketplace, 대규모 agent catalog, auto-commit류는 현재 NestClaw의 제품 방향과 맞지 않는다.
- 따라서 Stage 9 이후의 실제 채택 후보는 다음 세 묶음으로 요약된다:
  - `execution_readiness / qa_executable`
  - `completion_verification`
  - `model_routing_cleanup`
