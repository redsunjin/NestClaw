# Stage 8 실행안: 운영장애 대응 오케스트레이션 + 외부 RAG/MCP 연동

## 문서 목적
NestClaw의 다음 킬러 컨텐츠를 "운영장애 대응 자동화"로 고정하고,
외부 업무 지식 RAG와 MCP 도구(예: Redmine)를 안전하게 결합하는 실행 기준을 정의한다.

## 1) 킬러 컨텐츠 정의
핵심 시나리오:
1. 장애 신호 수집
2. 다중 소스 컨텍스트 조회(RAG)
3. 실행 가능한 액션 카드 생성
4. 승인/보안 검증
5. Redmine 티켓/작업 자동 반영(MCP)
6. 복구 상태 검증 + 보고

산출물은 "문서 요약"이 아니라 "실제 액션 가능한 운영 작업"이어야 한다.

## 2) 현재 NestClaw 기반에서 가능한 것 / 부족한 것
현재 가능한 것:
- `planner -> executor -> reviewer -> reporter` 오케스트레이션 체인
- RBAC + 승인 큐 + 감사 로그
- 상태머신 기반 실패 복구(재시도/승인 대기)
- SQLite/PostgreSQL 영속화

부족한 것:
- 외부 RAG 소스 어댑터(업무 지식/시스템 분석)
- MCP 기반 외부 실행 어댑터(Redmine 등)
- 장애 전용 입력 스키마와 액션 우선순위 엔진
- 운영장애 시나리오 전용 E2E 테스트

## 3) 목표 아키텍처 (Stage 8)
1. Incident Intake
- 입력: 알람/이벤트/운영자 신고
- 출력: 표준 Incident 객체

2. RAG Context Aggregator
- 외부 업무 지식 RAG에서 과거 처리사례/정책/런북 조회
- 시스템 분석 RAG에서 로그/토폴로지/이상 징후 요약 조회
- 결과를 신뢰도/최신성 기준으로 정렬

3. Action Planner
- 후보 액션 생성(예: 롤백, 재시작, 트래픽 우회, 담당자 호출)
- 각 액션에 위험도, 선행조건, 예상영향, 승인필요여부 부여

4. Approval & Policy Gate
- 위험도 High는 `NEEDS_HUMAN_APPROVAL` 강제
- 정책 위반 액션은 `BLOCKED_POLICY`로 차단

5. MCP Executor
- 승인된 액션만 실행
- Redmine MCP로 이슈 생성/갱신/코멘트/담당자 지정/상태 전환

6. Verification Reporter
- 실행 결과, 실패 원인, 잔여 리스크, 다음 액션 1개를 표준 리포트로 출력

## 4) Redmine MCP 최소 기능 맵
필수:
- `issue.create`
- `issue.update`
- `issue.add_comment`
- `issue.assign`
- `issue.transition`

권장:
- `project.list`
- `user.lookup`
- `issue.link_related`

## 5) RAG 연동 계약(초안)
업무 지식 RAG:
- 입력: `query`, `team`, `time_range`
- 출력: `evidence[]`(source, summary, confidence, timestamp)

시스템 분석 RAG:
- 입력: `incident_id`, `service`, `window`
- 출력: `signals[]`(symptom, suspected_component, confidence, evidence_ref)

NestClaw 내부 표준 컨텍스트:
```json
{
  "incident_id": "inc_20260304_001",
  "summary": "API latency spike and 5xx increase",
  "evidence": [
    {
      "source": "knowledge_rag",
      "confidence": 0.81,
      "text": "similar incident resolved by cache invalidation"
    },
    {
      "source": "system_rag",
      "confidence": 0.77,
      "text": "db connection pool saturation detected"
    }
  ]
}
```

## 6) 단계별 순서표 (24시간 연속 운영 기준)
Stage 8-1. 계약 고정
- RAG I/O 스키마 확정
- Redmine MCP 메서드 맵 확정
- 승인 필요 액션 분류표 확정

Stage 8-2. 어댑터 스켈레톤 구현
- RAG 클라이언트 인터페이스 2종
- Redmine MCP 실행 인터페이스 1종
- 실패/타임아웃 공통 핸들러

Stage 8-3. 오케스트레이션 결합
- Incident 전용 planner/executor 경로 추가
- 액션 카드 생성/승인/실행/보고 체인 연결

Stage 8-4. 검증 게이트
- Dry-run E2E (실행 없이 티켓 생성 시뮬레이션)
- Sandbox E2E (테스트 Redmine 프로젝트 대상)
- 장애 시나리오 회귀 세트(정상/차단/승인대기/실패복구)

Stage 8-5. 운영 시범
- 1개 서비스/1개 팀 대상 제한 도입
- 주간 리뷰로 정책/품질/승인 부담 조정

## 7) 전문가 그룹 역할 (Stage 8 기준)
- A01 Product Owner: 장애 자동화 범위/성과지표 고정
- A02 Workflow Engineer: Incident 상태머신/오케스트레이션 구현
- A03 LLM Orchestrator: 액션 카드 품질/재시도 경로 운영
- A04 Security Privacy: 승인 분류/차단 정책/비밀값 관리
- A05 UX Operations: 승인자 화면과 운영 알림 UX
- A06 QA Reliability: 장애 회귀 시나리오/릴리즈 게이트
- A07 Compliance Advisor: 로그 보존/접근통제 준수 검토
- A08 Domain SME: 액션 카드의 운영 현실성 검수

## 8) 성공 지표 (도입 1차)
- MTTA(인지시간) 30% 단축
- 초기 대응 티켓 생성 자동화율 70% 이상
- 승인 누락 0건
- 정책 위반 실행 0건
- 장애 리포트 재현성(근거 링크 포함) 95% 이상

## 9) 가드레일
- 승인 없는 고위험 액션 자동 실행 금지
- RAG 근거 없는 추측성 액션 실행 금지
- 민감정보가 포함된 외부 전송은 기본 차단
- 모든 MCP 호출은 actor/task/incident 단위로 감사로그 기록
