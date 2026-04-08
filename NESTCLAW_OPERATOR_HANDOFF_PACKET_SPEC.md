# NestClaw Operator Handoff Packet Spec

## 목적
- operator, upper agent, approver가 같은 execution evidence를 compact한 handoff packet 한 장으로 읽게 만든다.
- handoff packet은 새로운 truth source가 아니라 `agent.bundle`을 compact하게 재구성한 operator view model이다.

## Canonical Surfaces
- HTTP: `GET /api/v1/agent/handoff/{task_id}`
- CLI: `newclaw handoff --task-id <task_id> --actor-id <actor_id> --json`
- MCP: `agent.handoff`

## Packet Types
| packet_type | 의미 | 기본 owner |
| --- | --- | --- |
| `blocked` | runtime 또는 external dependency가 막혀 operator 개입이 필요한 상태 | `operator_or_integration_owner` |
| `approval_pending` | 승인 또는 정책 review가 필요한 상태 | `approver_admin` |
| `completed` | 보고서와 결과가 준비되어 handoff/closeout 가능한 상태 | `requester_or_operator` |
| `observe` | 아직 진행 중이라 관찰이 우선인 상태 | `requester_or_reviewer` |

## Canonical Fields
- `packet_version`
- `source_bundle_version`
- `packet_type`
- `task_id`
- `resolved_kind`
- `generated_at`
- `recommended_handoff_owner`
- `operator_summary`
- `planning`
- `execution`
- `approval`
- `report`
- `environment_readiness`
- `operator_actions`
- `bundle_ref`
- `markdown`

## Operator Summary
- `title`
- `requested_by`
- `status`
- `current_stage`
- `next_action`
- `last_event_at`
- `request_summary`
- `canonical_state`
- `canonical_reason_code`
- `detail_reason_code`
- `state_message`
- `run_mode`

## Role Gating
- packet은 기존 authorization 경계를 그대로 따른다.
- requester/reviewer는 approval summary만 받고, approver/admin만 approval action history detail을 본다.
- markdown rendering도 동일한 gated payload를 기반으로 생성한다.

## Rendering Policy
- JSON payload가 canonical source다.
- CLI plain output과 operator relay용 복사는 `markdown` field를 사용한다.
- markdown에는 secret/token/raw credential을 남기지 않는다.

## Decision Rules
- `approval_pending`: approval queue와 reason을 중심으로 본다.
- `completed`: report preview/raw artifact를 closeout 기준으로 본다.
- `blocked`: canonical reason code, detail reason, last error를 기준으로 unblock owner를 결정한다.
