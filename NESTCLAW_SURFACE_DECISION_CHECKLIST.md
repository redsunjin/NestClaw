# NestClaw Surface Decision Checklist

## Use This Before Adding Any New Surface

## 1. Surface Identity
- 이 표면은 `상위 agent용 호출면`인가, `인간 operator용 dashboard`인가?
- 둘을 동시에 하려는가?
  - 동시에 하려면 분리 설계가 먼저다.

## 2. Contract Reuse
- 기존 `agent.submit/status/events/recent/report`, `approval.*`, `catalog.*`, `capabilities`를 재사용하는가?
- 새 표면이 독립 planner/executor 경로를 만들지는 않는가?

## 3. Policy / Approval
- 기존 role policy를 그대로 따르는가?
- approval/audit을 우회하는 shortcut이 생기지 않는가?
- requester와 approver/admin의 제어면이 분리되는가?

## 4. Auditability
- status, events, approval history, report에 흔적이 남는가?
- 사용자가 본 결과와 system of record가 어긋나지 않는가?

## 5. Product Fit
- 이 표면이 NestClaw를 `control plane`으로 강화하는가?
- 아니면 `chat app`, `marketplace`, `agent hub`처럼 보이게 만드는가?

## 6. UI / UX Fit
- 인간용 표면이면 operator dashboard 역할을 강화하는가?
- 상태가 액션보다 먼저 보이는가?
- 고위험 제어면이 전면 노출되지 않는가?

## 7. Expansion Decision
### Proceed
- 기존 contract 재사용
- approval/audit 유지
- control plane 정체성 강화

### Review More
- 새 chat panel
- 새 governance surface
- live execution shortcut

### Reject
- 별도 human interactive TUI
- policy-bypassing dashboard action
- marketplace형 catalog expansion
