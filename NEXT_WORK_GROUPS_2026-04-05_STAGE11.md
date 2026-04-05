# Next Work Groups (2026-04-05, Stage 11)

## 목적
Stage 10 campaign이 완료되고 Stage 8 live readiness가 외부 env 부재로 계속 `BLOCKED`인 상태에서, NestClaw를 실제 pilot 운영 슬롯으로 넘기기 위한 `pilot operationalization` 묶음을 고정한다.

## 현재 판단
- `stage10-priority-campaign`은 G1~G4를 모두 완료했다.
- upper-agent integration surface와 MCP stdio baseline은 정리됐지만, 운영자 handoff와 external env handoff는 아직 문서/패킷이 흩어져 있다.
- 따라서 다음 단계는 planner breadth 확장이 아니라 `operator export, env profile, deployment profile, pilot acceptance`를 더 단단하게 만드는 Stage 11이다.

## 그룹 정의
### G1. External Env Handoff Profile
- 목표: Stage 8 sandbox/live readiness에 필요한 external env를 한 장의 canonical handoff profile로 묶고, 누락 여부를 빠르게 검증할 수 있게 만든다.
- 범위:
  - Stage 8 missing env를 목적/예시/owner 기준으로 정리한 handoff profile 추가
  - local validator 또는 점검 절차를 문서/스크립트로 고정
  - ops handoff에 필요한 최소 payload를 한 세트로 정리
- 완료 기준:
  - 운영자가 scattered doc 없이 external env handoff 요구사항을 한 문서에서 읽을 수 있다.
  - env 누락 여부를 재현 가능하게 점검할 수 있다.

### G2. Operator Handoff Packet Export
- 목표: 특정 task/approval/bundle을 operator에게 넘길 때 필요한 handoff packet을 markdown/json 형태로 쉽게 export할 수 있게 한다.
- 범위:
  - execution bundle 기반 handoff packet shape 정의
  - approval pending / blocked / done 각각에 필요한 요약 필드 고정
  - operator용 export surface 또는 문서 예시 추가
- 완료 기준:
  - 상위 agent가 operator에게 넘길 때 필요한 패킷 형식이 고정된다.

### G3. Deployment Profile Bootstrap
- 목표: local dev, sidecar operator, upper-agent host가 같은 방식으로 uvicorn + MCP stdio를 띄울 수 있게 bootstrap profile을 제공한다.
- 범위:
  - launch profile 예시
  - auth mode별 최소 startup guide
  - process health / restart 기준 정리
- 완료 기준:
  - repo 문서만으로 표준 배치 프로파일을 재현할 수 있다.

### G4. Pilot Acceptance Cycle
- 목표: pilot go/no-go 판단을 반복 가능한 acceptance cycle로 묶는다.
- 범위:
  - 현재 packet/runbook/evidence matrix를 acceptance checklist로 연결
  - blocked vs fail vs operational hold 해석 기준 고정
  - 필요하면 가벼운 script/contract 보강
- 완료 기준:
  - pilot acceptance 판단이 문서와 증적 기준으로 반복 가능하다.

## 권장 순서
1. G1
2. G2
3. G3
4. G4

## 현재 추천 포커스
- 현재 추천 포커스: `G1 External Env Handoff Profile`
- 이유:
  - Stage 8의 실제 blocker는 계속 external env handoff다.
  - Stage 10에서 upper-agent integration은 충분히 다듬었으므로, 다음 병목은 운영자/외부 시스템 handoff를 줄이는 것이다.
  - G1이 정리되면 G4 pilot acceptance와도 바로 연결된다.

## 운영 트랙 메모
- Stage 8 readiness 최신 canonical summary:
  - `STAGE8_QA_RERUN_STATUS_2026-04-05.md`
- latest readiness bundle baseline:
  - `reports/qa/stage8-readiness-bundle-20260405T034720Z.md`
- env가 준비되면 QA worktree에서 아래 명령을 재실행한다.
  - `cd /Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa`
  - `source .venv/bin/activate`
  - `bash scripts/run_stage8_readiness_bundle.sh`

## 연속 추진 Campaign
- `stage11-priority-campaign`
- 목표: G1 -> G2 -> G3 -> G4 순서로 pilot operationalization을 끊김 없이 추진한다.
