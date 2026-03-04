# Stage 8 Execution Checklist (2026-03-04)

## 목적
운영장애 대응 오케스트레이션(Stage 8)을 설계 단계에서 구현/운영 단계로 안전하게 전환하기 위한 주차별 실행 체크리스트다.

## 적용 범위
- 기준 문서: `INCIDENT_ORCHESTRATION_RAG_MCP_PLAN.md`
- 상세 설계: `STAGE8_DETAILED_DESIGN_2026-03-04.md`
- 실행 추적: `TASKS.md`

## KPI (Go/No-Go 기준)
- MTTA 30% 단축
- 초기 대응 티켓 자동화율 70% 이상
- 승인 누락 0건
- 정책 위반 실행 0건
- 근거 링크 포함 리포트 비율 95% 이상

## 운영 원칙
- 고위험 액션은 승인 없이 실행하지 않는다.
- 모든 액션은 evidence link를 포함한다.
- Dry-run 결과를 통과하기 전 Sandbox 실행을 금지한다.
- 주차 종료 시점에 증적(report/log/test)을 반드시 남긴다.

## Week 0 (2026-03-05 ~ 2026-03-06) 기준선 고정
- [ ] Stage 8 백로그를 `TASKS.md` 기준으로 확정
- [ ] 오너 할당(A01~A06 중심) 및 리뷰 슬롯(주 2회) 고정
- [ ] Redmine Sandbox 프로젝트/권한 범위 확정
- [ ] 운영장애 파일럿 대상 서비스 1개 확정

완료 기준:
- 실행 오너/일정/대상 서비스가 문서로 고정됨

증적:
- 회의 요약 1건
- 백로그 업데이트 커밋 1건

## Week 1 (2026-03-09 ~ 2026-03-13) 계약 고정
- [ ] Incident 입력/출력 스키마 확정
- [ ] Knowledge/System RAG I/O 계약 확정
- [ ] Redmine MCP 메서드별 payload 계약 확정
- [ ] 액션 카드 스키마 + 승인 분류표 확정
- [ ] Stage 8 계약 테스트(`tests/test_stage8_contract.py`) green

완료 기준:
- Stage 8 계약 QA가 PASS

증적:
- 계약 문서 diff
- 계약 테스트 실행 로그

## Week 2 (2026-03-16 ~ 2026-03-20) 어댑터 스켈레톤
- [ ] `app/incident_rag.py` 스켈레톤 추가
- [ ] `app/incident_mcp.py` 스켈레톤 추가
- [ ] timeout/retry/error 공통 포맷 추가
- [ ] Dry-run 모드 호출 경로 연결

완료 기준:
- 외부 연동 없이 mock 기반 end-to-end Dry-run 1건 성공

증적:
- 단위 테스트/로그

## Week 3 (2026-03-23 ~ 2026-03-27) 오케스트레이션 결합
- [ ] Incident 전용 planner 경로 추가
- [ ] 승인/정책 게이트와 action card 결합
- [ ] reviewer/reporter에 incident 결과 포맷 반영
- [ ] 실패 시 `FAILED_RETRYABLE -> NEEDS_HUMAN_APPROVAL` 전환 검증

완료 기준:
- 정상/차단/승인대기/실패복구 4경로 재현

증적:
- 런타임 테스트 로그
- 샘플 리포트 2건

## Week 4 (2026-03-30 ~ 2026-04-03) 품질게이트 고정
- [ ] Stage 8 QA 스크립트/테스트를 파이프라인에 포함
- [ ] `scripts/run_dev_qa_cycle.sh 8` 기준 green
- [ ] 문서 감사 + 계약 테스트 + 런타임 테스트 결과 저장

완료 기준:
- Stage 8 게이트가 반복 실행에서 안정적으로 PASS/SKIP 규칙 준수

증적:
- `reports/qa/` 결과 리포트

## Week 5 (2026-04-06 ~ 2026-04-10) Sandbox 운영 검증
- [ ] Redmine Sandbox에 incident ticket lifecycle 재현
- [ ] 승인자 실제 승인 흐름 검증(approve/reject)
- [ ] 감사 로그의 actor/task/incident 연계성 검증

완료 기준:
- 티켓 생성/갱신/전환 + 승인 흐름 + 감사추적이 일관되게 동작

증적:
- Sandbox 실행 로그
- 리뷰 체크리스트 결과

## Week 6-7 (2026-04-13 ~ 2026-04-24) 파일럿/안정화
- [ ] 서비스 1개/팀 1개 파일럿 운영
- [ ] KPI 주간 리뷰(2회 이상)
- [ ] false positive/승인부담/실패복구 튜닝 반영
- [ ] Go/No-Go 회의록 확정

완료 기준:
- KPI 기준 충족 시 확장 승인, 미충족 시 범위 축소/보완 계획 확정

증적:
- 파일럿 결과 리포트
- Go/No-Go 의사결정 기록
