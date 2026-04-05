# Next Work Groups (2026-04-05)

## 목적
Stage 9 campaign이 완료되고 Stage 8 live readiness가 외부 env 부재로 `BLOCKED`인 상태에서, NestClaw를 `closed orchestration runtime + operator dashboard` 방향으로 계속 강화할 다음 구현 묶음을 고정한다.

## 현재 판단
- `stage9-priority-campaign`은 G1~G4를 모두 완료했다.
- 최신 Stage 8 QA rerun baseline은 `BLOCKED`이며, local DB/worktree 문제는 해소됐고 외부 env 부족만 남았다.
- 따라서 다음 작업은 새로운 live rehearsal 재시도가 아니라, 상위 agent 통합과 operator evidence 흐름을 더 단단하게 만드는 `stage10-priority-campaign`을 여는 것이다.
- Stage 10의 기준은 기능 breadth보다 `contract, auditability, operator handoff, transport hardening`이다.

## 그룹 정의
### G1. Canonical Execution Bundle Export
- 목표: task/incident 실행 결과를 `status + events + report + approval snapshot + capability snapshot` 한 번에 읽을 수 있는 canonical bundle로 노출한다.
- 범위:
  - orchestration service에 task 단위 execution bundle payload 추가
  - HTTP / CLI / MCP에 동일한 bundle 조회 표면 추가
  - approval detail 접근 권한이 없는 actor에는 summary만 노출하고, approver/admin에는 full detail을 포함
  - bundle contract 회귀 테스트 추가
- 완료 기준:
  - 상위 agent가 `submit -> observe -> report` 뒤 handoff/export를 한 payload로 처리할 수 있다.
  - operator가 특정 task의 상태, 실행 흔적, 승인 상태, 보고서를 한 번에 가져올 수 있다.
  - HTTP/CLI/MCP가 같은 bundle shape를 반환한다.

### G2. Role-Gated Operator Surface Hardening
- 목표: dashboard가 requester, reviewer, approver/admin에게 같은 화면을 보여주지 않도록 시각적/기능적 gating을 강화한다.
- 범위:
  - `/console`에서 requester에게 고위험 governance control을 숨기거나 fold 뒤로 이동
  - approval/draft/apply/rollback 버튼 가시성을 role별로 정리
  - operator copy와 empty state를 역할 중심으로 다듬기
- 완료 기준:
  - requester는 실행/조회 중심, approver/admin은 governance 중심으로 읽힌다.
  - dashboard가 다기능 업무 앱처럼 보이지 않는다.

### G3. Readiness / Error Taxonomy Normalization
- 목표: runtime, readiness, adapter, dashboard가 `PASS/FAIL/BLOCKED/SKIP/degraded`를 같은 의미로 해석하게 만든다.
- 범위:
  - Stage 8 readiness와 runtime error reason code 정렬
  - env-blocked, policy-blocked, approval-pending, retryable-failure taxonomy 문서/payload 보강
  - capability manifest/readiness summary에 canonical reason code 추가
- 완료 기준:
  - operator와 upper agent가 `기능 오류`와 `운영 환경 미준비`를 혼동하지 않는다.
  - report/status/bundle의 blocked/degraded 이유가 같은 vocabulary를 쓴다.

### G4. MCP Transport / Deployment Hardening
- 목표: NestClaw MCP를 상위 agent가 반복적으로 붙일 수 있도록 packaging/transport/auth 가이드를 고정하고 smoke를 보강한다.
- 범위:
  - MCP startup/runtime guidance 정리
  - remote/stdio transport 전제와 auth boundary 문서화
  - 배포/운영용 최소 smoke 및 예제 호출 정리
- 완료 기준:
  - 상위 agent 통합자가 repo 문서만으로 MCP 연결 경계를 이해할 수 있다.
  - stdio baseline과 운영 배포 경계가 문서/테스트로 정리된다.

## 권장 순서
1. G1
2. G2
3. G3
4. G4

## 현재 추천 포커스
- 현재 추천 포커스: `G1 Canonical Execution Bundle Export`
- 이유:
  - product posture 기준으로 다음 우선순위는 breadth가 아니라 audit/export/agent handoff quality다.
  - bundle export는 새 planner를 만드는 작업이 아니라 기존 contract를 묶어 control plane 완성도를 높이는 작업이다.
  - 이후 G2/G3/G4가 모두 이 bundle을 기준 payload로 재사용할 수 있다.

## 운영 트랙 메모
- Stage 8 live readiness는 운영 트랙에서 별도 관리한다.
- 최신 canonical summary:
  - `STAGE8_QA_RERUN_STATUS_2026-04-05.md`
- env가 준비되면 QA worktree에서 아래 명령을 재실행한다.
  - `cd /Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa`
  - `source .venv/bin/activate`
  - `bash scripts/run_stage8_readiness_bundle.sh`

## 연속 추진 Campaign
- `stage10-priority-campaign`
- 목표: G1 -> G2 -> G3 -> G4 순서로 operator evidence와 upper-agent integration hardening을 끊김 없이 추진한다.
