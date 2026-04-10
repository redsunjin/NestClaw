# NestClaw Pilot Acceptance Cycle

## 목적
- Stage 11에서 정리된 env handoff, operator handoff, deployment bootstrap, pilot evidence를 반복 가능한 acceptance loop로 묶는다.
- 상위 agent, operator, approver가 같은 문서 세트와 같은 판단 vocabulary로 `GO / Conditional Go / NO-GO / operational hold`를 결정하게 만든다.
- `BLOCKED`, `FAIL`, `operational hold`를 구분해 운영 blocker를 코드 failure처럼 오해하지 않게 한다.

## Canonical Inputs
| 입력 | 용도 | 최신 기준 |
| --- | --- | --- |
| `NESTCLAW_OPERATOR_HANDOFF_PACKET_SPEC.md` | operator/upper-agent compact handoff vocabulary | `agent.handoff`, `packet_type`, `canonical_state` |
| `STAGE8_EXTERNAL_ENV_HANDOFF_PROFILE_2026-04-05.md` | required external env contract | missing env, owner, validator 규칙 |
| `STAGE8_BLOCKED_TO_RESUMED_RUNBOOK_2026-04-05.md` | Stage 8 blocked resume 절차 | resume command, PASS/BLOCKED/FAIL handling |
| `NESTCLAW_PILOT_EVIDENCE_MATRIX_2026-04-05.md` | 현재 확보 증적과 빈 구멍 | code regression vs operational blocker 분리 |
| `NESTCLAW_PILOT_GO_NO_GO_PACKET_2026-04-05.md` | 현재 pilot 권고안 | current recommendation, re-decision rule |
| `STAGE8_QA_RERUN_STATUS_2026-04-05.md` | latest readiness baseline summary | current readiness state, remaining blockers |
| `reports/qa/cycle-*.md` | 최신 전체 회귀 evidence | code/runtime regression baseline |
| `reports/qa/stage8-readiness-bundle-*.md` | Stage 8 readiness 최종 판정 | live slot readiness source |

## Decision Vocabulary
### Evidence Classification
- `PASS`: 필요한 증적이 존재하고 해당 축이 통과했다.
- `BLOCKED`: required env, owner, approval window, external dependency가 비어 있어 다음 검증으로 못 넘어간다.
- `FAIL`: required input은 존재하지만 runtime, integration, policy, rehearsal이 실패했다.
- `OPERATIONAL_HOLD`: 코드/증적은 pilot 가능 수준이지만 일정, 승인자 부재, freeze, stale evidence 같은 운영 사유로 개시를 보류한다.

### Pilot Decision
- `GO`: external live pilot을 열 수 있다.
- `Conditional Go`: 내부 dry-run, operator walkthrough, upper-agent rehearsal만 허용한다.
- `NO-GO`: external live pilot을 열지 않는다.

## Canonical Mapping Rules
1. latest dev-QA cycle이 `FAIL`이면 pilot decision은 `NO-GO`다.
2. Stage 8 readiness bundle이 `BLOCKED`이면 pilot decision은 `NO-GO`다. 이 경우 원인은 운영 입력 부족으로 기록하고 코드 failure로 올리지 않는다.
3. readiness bundle 또는 sandbox/live rehearsal이 `FAIL`이면 pilot decision은 `NO-GO`다.
4. code/runtime evidence가 `PASS`이고 live evidence가 아직 없지만 internal dry-run은 가능한 경우 `Conditional Go`다.
5. required evidence가 모두 `PASS`지만 owner/approver/schedule/freeze 조건 때문에 시작을 늦추는 경우 evidence classification은 `OPERATIONAL_HOLD`이고 pilot decision은 `GO deferred`로 기록한다.
6. `OPERATIONAL_HOLD`는 `BLOCKED`와 다르다. hold는 필요한 값과 증적이 이미 존재하지만 운영 판단으로 멈춘 상태다.

## Acceptance Loop
1. 최신 전체 회귀를 확보한다.
2. latest Stage 8 rerun summary와 readiness bundle 상태를 읽는다.
3. 외부 env handoff completeness를 validator로 확인한다.
4. operator handoff가 필요한 task가 있으면 `agent.handoff` packet을 생성한다.
5. evidence matrix와 go/no-go packet을 현재 기준으로 업데이트한다.
6. 아래 질문에 답한다.
   - 전체 코드 회귀는 PASS인가
   - Stage 8 readiness는 PASS / BLOCKED / FAIL 중 무엇인가
   - sandbox/live evidence가 존재하는가
   - owner, approver, execution slot이 지정됐는가
   - stale evidence 때문에 판단을 미뤄야 하는가
7. classification을 먼저 적는다.
   - `BLOCKED`, `FAIL`, `OPERATIONAL_HOLD`, `PASS`
8. 그 다음 pilot decision을 적는다.
   - `GO`, `Conditional Go`, `NO-GO`
9. 결과와 다음 액션을 canonical 문서에 남긴다.

## Output Recording Rules
- `NO-GO`: go/no-go packet에 이유와 missing input을 적고, evidence matrix에 blocker row를 갱신한다.
- `Conditional Go`: internal-only scope를 명시하고 external side effect 금지를 같이 적는다.
- `GO`: latest readiness bundle, sandbox report, live report 경로를 go/no-go packet에 승격한다.
- `OPERATIONAL_HOLD`: hold owner, hold reason, resume trigger를 go/no-go packet 또는 operator handoff packet에 적는다.

## Current Baseline (2026-04-10)
- current dev-QA baseline: latest Stage 11 cycle PASS
- current Stage 8 readiness baseline: `BLOCKED`
- current pilot recommendation: `NO-GO for external live pilot`
- current internal recommendation: `Conditional Go` for dry-run / operator walkthrough
- current blocker class: `BLOCKED` due to missing external env

## Guardrails
- secret/token 값은 acceptance 문서나 handoff packet markdown에 직접 적지 않는다.
- `BLOCKED`와 `FAIL`을 섞지 않는다.
- `GO`는 latest readiness PASS 증적 없이 선언하지 않는다.
- `Conditional Go`는 internal-only scope와 external write 금지를 같이 적는다.
- `OPERATIONAL_HOLD`는 evidence 부족이 아니라 운영 판단 보류일 때만 쓴다.
