# Next Work Groups (2026-03-13)

## 목적
지금까지 만든 Web Console, agent facade, tool registry, approval surface를 다음 실행 단위로 묶어서 우선순위를 명확하게 고정한다.

## 그룹 정의
### G1. Operator Surface Completion
- 목표: 사람이 `무엇이 최근에 일어났는지`와 `다음에 뭘 눌러야 하는지`를 바로 이해하게 만든다.
- 범위:
  - 최근 task / 최근 approval 히스토리
  - 결과 report 미리보기
  - approval comment/history drill-down
  - polling 또는 새로고침 UX 정리
- 완료 기준:
  - Web Console만으로 최근 흐름 추적 가능
  - operator가 Swagger 없이 기본 운영 동선을 수행 가능

### G2. Planning and Execution Maturity
- 목표: 현재 1-step 수준의 planner를 실제 multi-step tool planning으로 올린다.
- 범위:
  - tool registry 기반 후보 선택
  - plan provenance 기록
  - multi-step execution loop
  - dry-run/live execution matrix 정리
- 완료 기준:
  - 하나의 요청에서 2개 이상 tool을 계획적으로 선택/실행 가능

### G3. Tool Governance and Lifecycle
- 목표: 도구 추가와 운영을 product surface로 닫는다.
- 범위:
  - draft review/apply/rollback
  - tool 검증 harness
  - runtime overlay artifact 정리 자동화
  - capability schema versioning
- 완료 기준:
  - 새 도구 등록/검증/반영/철회를 반복 가능한 절차로 수행 가능

### G4. Runtime and Live Readiness
- 목표: 로컬/QA 수준을 넘어서 실제 운영 검증 공백을 줄인다.
- 범위:
  - sandbox/live rehearsal 증적
  - provider live invocation 확대
  - auth/SSO 운영 UX 보강
  - persistence/load/concurrency 리허설
- 완료 기준:
  - dry-run이 아닌 live evidence가 누적되고 운영 안정성 리스크가 줄어듦

## 권장 순서
1. G2
2. G1
3. G3
4. G4

## 현재 판단
- 현재 추천 포커스: `G2`
- 이유:
  - 현재 목표는 operator surface보다 `AI-first orchestration agent` 정렬이 우선이다.
  - planner/tool ecosystem이 주 실행 경로가 되기 전에는 NestClaw가 tool server나 workflow app처럼 보일 위험이 더 크다.
  - G1 후속은 필요하지만, planner provenance를 보여줄 실체가 먼저 생겨야 UX도 방향이 맞는다.

## 즉시 이어갈 작업 후보
1. `agent-s8-llm-planner` MWU 생성 및 AI-first planner acceptance 고정
2. tool registry 기반 후보 선택과 plan provenance schema 정의
3. degraded mode 전환 기준과 audit/event contract 고정
4. 그 다음 planner provenance를 UI에 표시
