# NestClaw Assistive Chat Panel Review (2026-04-04)

## 결론
- 별도의 인간용 interactive TUI는 새 제품 표면으로 만들지 않는다.
- 사람용 대화형 입력이 필요하면 `/console` 안의 assistive chat panel로만 검토한다.
- chat panel은 독립 실행기나 독립 정책면이 아니라, 기존 `agent.submit/status/events`, `agent.recent`, `agent.report`, `approval.*`, `catalog.manifest`를 감싸는 보조 입력면이어야 한다.

## 왜 별도 TUI를 만들지 않는가
- NestClaw의 코어 역할은 orchestration backend다.
- 사람용 주 운영면은 승인, 감사, 상태 추적을 위한 dashboard다.
- 별도 TUI를 추가하면 같은 runtime 위에 또 하나의 사람용 주 표면이 생겨 계약, 역할, 승인 정책이 쉽게 갈라진다.
- 상위 대화형 에이전트와 다른 terminal/client는 이미 HTTP/CLI/MCP로 같은 service 계층에 접근할 수 있어야 한다.

## Chat Panel의 허용 역할
- 자연어 요청을 받아 기존 `agent.submit` payload로 정리한다.
- 현재 task의 `status/events/report`를 대화형으로 요약해 보여준다.
- `NEEDS_HUMAN_APPROVAL` 상태를 설명하고, operator가 승인 큐를 보도록 연결한다.
- capability/readiness 상태를 설명하고, env 부족이나 blocked reason을 자연어로 풀어준다.

## Chat Panel의 금지 역할
- 별도의 planner/executor 경로를 직접 만들지 않는다.
- approval/policy/audit contract를 우회하지 않는다.
- tool draft apply, live execution, admin governance를 chat 전용 단축 경로로 노출하지 않는다.
- chat transcript를 시스템 오브 레코드로 취급하지 않는다.
  - 시스템 오브 레코드는 여전히 task, event, report, approval history다.

## 서비스 확장 영향
### 1. 운영 구조 영향
- 장점:
  - operator가 복잡한 API 구조를 몰라도 자연어로 현재 상태를 해석할 수 있다.
  - requester와 approver가 같은 dashboard 안에서 다른 깊이의 도움말을 받을 수 있다.
- 리스크:
  - dashboard가 “운영 대시보드”에서 “대화형 앱”으로 오해될 수 있다.
  - 사람이 chat에서 직접 승인/실행이 다 되는 것처럼 느끼면 governance 경계가 흐려진다.

### 2. 성능 영향
- chat panel이 매 턴마다 `recent`, `status`, `events`, `capabilities`를 모두 재조회하면 불필요한 read load가 늘어난다.
- 초기 구현은 다음 제한을 둔다.
  - `status/events` polling은 현재 선택 task에만 제한
  - `recent`는 명시 갱신 또는 느린 주기 갱신
  - `report`는 완료 task에만 요청
  - `capabilities`는 화면 로드와 role 변경 시에만 재조회
- 확장 전제:
  - 고빈도 대화 흐름이 늘면 polling보다 SSE/streaming 검토가 필요하다.

### 3. 보안/정책 영향
- actor context는 기존 dashboard와 동일해야 한다.
- requester chat은 requester 권한을 넘지 못한다.
- approver/admin 전용 액션은 기존 role gating을 그대로 따른다.
- chat transcript에는 비밀값, live credential, raw token을 남기지 않는다.

## 구현 권고 순서
1. `read-only assistive panel`
   - 현재 task 상태, planner provenance, readiness, blocked reason만 자연어로 요약
2. `submit helper`
   - 자연어를 기존 submit form에 주입하거나, 같은 endpoint로 제출
3. `observe helper`
   - `status/events/report`를 대화형으로 다시 설명
4. `approval guidance`
   - 승인 필요 이유와 다음 human action을 설명
5. `high-risk control review`
   - approve/reject, draft apply 같은 고위험 액션을 chat shortcut으로 둘지 별도 검토

## 구현 시 절대 기준
- 같은 runtime contract를 재사용한다.
- 같은 actor/role policy를 재사용한다.
- 같은 audit trail을 재사용한다.
- chat panel은 입력 보조면이지, 새로운 orchestration surface가 아니다.

## 도입 판단
- 도입 자체는 `조건부 추천`이다.
- 먼저 필요한 것은 agent-facing CLI/MCP parity와 operator dashboard 정리다.
- 그 둘이 안정화된 뒤에만 assistive chat panel을 소형 PoC로 붙이는 것이 맞다.
- 따라서 현재 단계에서는 `review complete / implementation deferred`가 적절하다.
