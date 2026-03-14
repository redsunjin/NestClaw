# Priority Campaign Protocol (2026-03-15)

## 목적
우선순위 백로그를 하나의 MWU로 끝내지 않고, 여러 MWU가 `끊김 없이` 이어지도록 상위 캠페인 레이어를 선언한다.

이 문서는 [EXPERT_AGENT_OPERATING_PROTOCOL_2026-03-13.md](/Users/Agent/ps-workspace/NestClaw_works/worktrees/nestclaw-ideation/EXPERT_AGENT_OPERATING_PROTOCOL_2026-03-13.md) 위에 얹히는 상위 절차다.  
MWU가 `한 단위의 게이트`라면, Priority Campaign은 `여러 MWU를 어떤 순서로 계속 이어갈지`를 고정한다.

## 선언
- 연속 추진이 필요한 우선순위 묶음은 `work/priority_campaigns/<campaign_id>/campaign.json`으로 선언한다.
- Campaign의 각 항목은 정확히 하나의 MWU로 수행한다.
- Campaign은 `pending -> in_progress -> completed` 상태만 가진다.
- 동시에 `in_progress`인 campaign item은 하나만 허용한다.
- 현재 item의 MWU가 `DONE`이 되면, 다음 pending item을 즉시 준비해 연속 진행한다.
- Campaign은 명시적 stop condition이 없는 한 멈추지 않는다.

## Stop Condition
1. 현재 MWU의 `Evaluate` gate 실패
2. 정책/승인 이슈가 남아서 자동 진행 기준을 충족하지 못함
3. live credential / sandbox env가 필수인데 없어서 다음 item 실행이 실질적으로 불가능함
4. 사용자 또는 릴리즈 오너가 수동 중단을 선언함

## 역할 연결
- A01/A03: 다음 campaign item의 goal과 acceptance를 고정
- A04: review gate 통과 여부 확인
- A02: implement
- A06: evaluate
- A09: sync 이후 campaign advance 수행

## 표준 명령
```bash
bash scripts/run_priority_campaign.sh status <campaign_id>
bash scripts/run_priority_campaign.sh start-next <campaign_id> 8
bash scripts/run_priority_campaign.sh advance <campaign_id> <item_id> <unit_id> 8
```

## 규칙
- Campaign advance는 현재 MWU의 `WORK_UNIT.md`가 `DONE`일 때만 허용한다.
- `advance`는 완료된 item을 `completed`로 마킹하고, 다음 pending item이 있으면 자동으로 `in_progress`로 올린 뒤 expert workflow `prepare`를 호출한다.
- 다음 item이 없으면 Campaign은 완료 상태다.

## 현재 적용 Campaign
- `stage8-priority-campaign`
- 목표: G2 -> G1 -> G3 -> G4 우선순위를 policy-compatible 방식으로 연속 추진
