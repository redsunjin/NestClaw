# Next Work Groups (2026-03-17)

## 목적
Stage 8 내부 구현 backlog가 모두 닫힌 뒤, 외부 sandbox/live env 부재로 멈춘 readiness와 별개로 바로 이어서 실행할 후속 구현 우선순위를 고정한다.

## 현재 판단
- `stage8-priority-campaign`은 완료 상태다.
- 최신 readiness bundle은 외부 env 5개 미설정 때문에 `BLOCKED`이며, 동일 환경에서 재실행해도 상태는 바뀌지 않는다.
- 따라서 다음 작업은 `live rehearsal 재시도`가 아니라, broader execution agent로 가는 다음 구현 묶음을 campaign으로 선언하는 것이다.
- 외부 env가 준비되면 Stage 8 readiness bundle은 운영 트랙에서 별도로 재개한다.

## 그룹 정의
### G1. Common Planner / Executor Convergence
- 목표: task와 incident가 같은 registry 기반 planner/executor 루프를 공유하게 만든다.
- 범위:
  - `planned_actions` 생성 로직과 실행 디스패치의 공통 helper 추출
  - task/incident action descriptor shape 정렬
  - execution binding과 prior-result handoff 규칙 공통화
  - 공통 planner/executor 테스트 추가
- 완료 기준:
  - task와 incident가 공통 planner/executor helper를 사용한다.
  - `planned_actions + planning_provenance + action_results` 계약이 workflow 간 일관된다.
  - 공통 helper 회귀를 잡는 runtime/contract 테스트가 존재한다.

### G2. Incident AI Reasoning Expansion
- 목표: incident path를 deterministic baseline에서 AI-first planning baseline으로 확장한다.
- 범위:
  - incident planner에 model registry/provider selection 연결
  - incident context 기반 multi-step plan 초안과 deterministic fallback 추가
  - incident 보고/알림 payload에 planner rationale 반영
  - fallback/degraded mode provenance 정교화
- 완료 기준:
  - incident도 task와 유사한 AI planner baseline을 가진다.
  - fallback 이유와 provider selection이 status/event에서 관찰 가능하다.
  - dry-run 환경에서 2개 이상 action 계획이 가능하다.

### G3. Operator Action Transparency
- 목표: operator가 계획, binding, 실행 결과를 UI에서 바로 해석할 수 있게 만든다.
- 범위:
  - quickstart/console에 action sequence와 binding preview 노출
  - tool execution 결과, approval rationale, live/dry-run badge 정리
  - 실패/blocked action의 drill-down 보강
- 단계 순서:
  1. `G3-S1 Surface Parity`
     - HTTP에 이미 있는 `recent/report/approval detail/capabilities` 수준의 제어면을 CLI/MCP에도 맞춘다.
     - 상위 agent가 한 표면에서 `submit -> observe -> approval -> report` 루프를 닫을 수 있어야 한다.
  2. `G3-S2 Dashboard Operatorization`
     - `/console` 상단에 capability/readiness summary를 노출한다.
     - role별로 고위험 제어면을 시각적으로 gating한다.
     - dashboard는 실행앱이 아니라 operator dashboard라는 성격을 더 분명히 한다.
  3. `G3-S3 Assistive Chat Panel Review`
     - 별도의 인간용 interactive TUI는 만들지 않는다.
     - 대시보드에 chat panel이 필요하면 기존 runtime contract를 감싸는 보조 입력면으로만 검토한다.
     - approval/policy/audit contract를 우회하는 독립 실행면은 금지한다.
     - 검토 문서: `NESTCLAW_ASSISTIVE_CHAT_PANEL_REVIEW_2026-04-04.md`
- 검증 규칙:
  - 각 단계가 끝날 때마다 전체 회귀를 다시 실행한다.
  - 권장 기준:
    - `python3 -m unittest`
    - `bash scripts/run_dev_qa_cycle.sh 9`
- 완료 기준:
  - operator가 Swagger 없이도 왜 이 action이 선택됐고 무엇이 실행됐는지 추적할 수 있다.
  - task/incident 모두 planned action 결과를 같은 UX로 확인할 수 있다.
  - 상위 agent용 CLI/MCP surface와 dashboard surface가 역할상 충돌하지 않는다.

### G4. Pilot Readiness Pack
- 목표: 외부 운영 슬롯이 열렸을 때 바로 실행할 수 있는 pilot/go-no-go 패키지를 고정한다.
- 범위:
  - env contract와 credential handoff checklist 문서화
  - Stage 8 blocked -> resumed 절차 명시
  - pilot evidence matrix와 go/no-go 문서 초안 작성
  - 운영 재실행 명령과 expected artifact 정리
- 완료 기준:
  - 외부 env가 준비되면 재탐색 없이 live readiness/pilot 세션을 실행할 수 있다.
  - 남은 운영 리스크와 필요한 증적이 문서로 고정된다.

## 권장 순서
1. G1
2. G2
3. G3
4. G4

## 현재 추천 포커스
- 현재 추천 포커스: `G1`
- 이유:
  - Stage 8에서 task/incident 계약 수렴은 끝났지만, planner/executor core는 아직 `app/main.py`에 workflow별 중복이 남아 있다.
  - incident AI planner를 넣기 전에 공통 실행 루프를 먼저 정리해야 fallback, binding, audit 계약이 흔들리지 않는다.
  - UI 고도화도 공통 action loop가 먼저 정리돼야 surface만 늘리고 계약이 갈라지는 문제를 피할 수 있다.

## 병행 UI/Surface 트랙 메모
- G1이 planner/executor core를 정리하는 주축인 것은 유지한다.
- 다만 상위 agent 통합과 operator dashboard 정리는 core와 병행해서 진행할 수 있다.
- 현재 즉시 실행 가능한 세부 순서는 `G3-S1 -> G3-S2 -> G3-S3(review only)`다.
- 현재 진행 상태:
  - `G3-S1` 완료: HTTP/CLI/MCP surface parity 반영
  - `G3-S2` 완료: dashboard capability/readiness summary와 role gating 반영
  - `G3-S3` 완료(검토): assistive chat panel 경계와 도입 기준 문서화

## 운영 트랙 메모
- Stage 8 live readiness는 계속 `BLOCKED`다.
- 재개 조건:
  - `NEWCLAW_STAGE8_SANDBOX_ENABLED`
  - `NEWCLAW_STAGE8_SANDBOX_BASE_URL`
  - `NEWCLAW_STAGE8_SANDBOX_PROJECT`
  - `NEWCLAW_STAGE8_LIVE_ENABLED`
  - `NEWCLAW_REDMINE_MCP_ENDPOINT`
- 재개 명령:
  - `cd /Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation-qa`
  - `source .venv/bin/activate`
  - `bash scripts/run_stage8_readiness_bundle.sh`

## 연속 추진 Campaign
- `stage9-priority-campaign`
- 목표: G1 -> G2 -> G3 -> G4 순서로 Stage 9 broader execution agent 기반을 끊김 없이 준비한다.
