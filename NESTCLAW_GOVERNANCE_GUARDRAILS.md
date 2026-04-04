# NestClaw Governance Guardrails

## 1. Purpose
- 이 문서는 NestClaw가 `조직용 orchestration control plane`이라는 제품 정체성을 벗어나지 않도록 확장 허용선과 금지선을 고정한다.

## 2. Must Preserve
- 상위 agent가 호출하는 backend 계층 구조
- 인간 승인과 감사 이력
- role-based control policy
- curated capability registry
- deterministic blocked / approval / report contract

## 3. Explicitly Disallowed
- 별도 human interactive TUI를 새 primary surface로 키우는 것
- dashboard chat이 approval, policy, audit contract를 우회하는 것
- tool catalog를 marketplace처럼 무제한 확장하는 것
- requester 권한으로 고위험 admin/approval action을 노출하는 것
- `DONE` 이전에 결과를 추정해 완료처럼 응답하는 UX

## 4. High-Risk Surfaces
- `approve`
- `reject`
- `catalog.apply_draft`
- `catalog.rollback_tool`
- live execution

규칙:
- 기본은 human-or-elevated-only
- shortcut을 만들더라도 기존 approval/audit trail을 재사용해야 한다
- 별도 chat command, hidden endpoint, client-side bypass를 허용하지 않는다

## 5. Chat / Dashboard Rule
- dashboard 안의 chat panel은 허용될 수 있다.
- 단, 역할은 `assistive input surface`로 제한한다.
- chat panel은 기존 `submit/status/events/report`를 감싸는 보조면이어야 한다.
- chat panel이 독립 planner/executor처럼 행동하면 금지다.

## 6. Catalog Rule
- catalog는 curated registry다.
- draft -> validate -> apply -> rollback 흐름을 유지한다.
- 공개 plugin 생태계, self-serve marketplace, 무제한 agent pack 노출은 비목표다.

## 7. Surface Rule
- 새 표면은 기존 runtime contract를 재사용해야 한다.
- 새 표면이 approval/audit semantics를 바꾸면 도입 금지다.
- 새 표면이 역할을 늘리는지, 단지 접근 방법을 늘리는지 구분해야 한다.

## 8. Drift Signals
- 문서가 NestClaw를 `agent hub`, `agent collection`, `main chat app`처럼 설명한다.
- dashboard가 상태/승인면보다 작업 앱처럼 커진다.
- catalog가 capability registry보다 agent marketplace처럼 보인다.
- 상위 agent와 NestClaw가 planner 주체를 두고 경쟁하는 문구가 생긴다.

## 9. Required Review Before Expansion
- product positioning과 충돌하지 않는가
- 기존 role policy를 재사용하는가
- approval/audit trail이 유지되는가
- live execution 위험이 늘어나는가
- GUI가 operator dashboard 성격을 잃는가
