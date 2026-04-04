# NestClaw Operator Dashboard Principles

## 1. 역할 정의
- NestClaw GUI는 primary workbench가 아니다.
- NestClaw GUI는 승인, 감사, 상태 확인, planner provenance 확인을 위한 operator dashboard다.
- 실제 자연어 대화와 작업 위임 UX의 주체는 상위 대화형 에이전트가 될 수 있다.
- 별도 인간용 TUI를 대체하는 표면으로 키우지 않는다.
- dashboard 안에 chat 기능이 들어오더라도 operator flow를 보조하는 수준으로 제한한다.

## 2. Dashboard First Principles
### 2.1 상태가 액션보다 먼저다
- 첫 화면에서 보여야 하는 것은 "지금 무슨 일이 벌어지고 있는가"다.
- 가장 먼저 보이는 정보:
  - 현재 task 상태
  - resolved kind
  - planner provenance
  - approval 필요 여부
  - report preview

### 2.2 고위험 제어면은 뒤로 간다
- `approve/reject/apply/rollback/live`는 자주 누르는 버튼이 아니다.
- 따라서 보조 운영면 또는 fold panel 뒤에 두는 편이 맞다.

### 2.3 내부 설계 용어를 사용자 헤드라인에 노출하지 않는다
- `surface`, `provenance`, `overlay`, `registry` 같은 단어는 내부 용어다.
- 화면 제목은 업무 용어로 쓴다.
- 예:
  - 좋음: `계획, 승인, 실행을 한눈에 보는 대시보드`
  - 나쁨: `계획, 승인, 실행 흔적을 읽는 운영면`

### 2.4 상위 에이전트와의 역할 분리를 반영한다
- Quickstart는 "간단 실행 + 결과 확인"
- Console은 "승인/감사/운영 판단"
- Dashboard는 agent를 대체하지 않고 감독한다.
- Chat panel이 들어오더라도 "운영 보조 입력면"으로 남아야 한다.

## 3. Information Hierarchy
### 3.1 Primary Zone
- 현재 사용자/역할
- 현재 task
- planner provenance
- approval detail
- report preview

### 3.2 Secondary Zone
- recent history
- approval queue
- tool catalog
- tool draft governance
- raw trace/log

### 3.3 숨겨야 하는 것
- 드물게 쓰는 admin/governance control
- 시스템 내부 용어 중심 패널
- 빈 상태에서 의미 없는 보조 카드

## 4. Language Policy
- 제목은 업무 언어로 쓴다.
- 한국어 헤드라인에는 번역투를 피한다.
- 단어는 짧게, 상태는 분명하게, 설명은 한 문장으로 끝낸다.
- 줄바꿈은 단어 단위로만 일어나야 한다.

권장 예:
- `계획, 승인, 실행을 한눈에 보는 대시보드`
- `현재 실행 상태`
- `승인이 필요한 작업`
- `최근 작업`

비권장 예:
- `운영면`
- `실행 흔적`
- `상태 관측 surface`

## 5. Visual Policy
### 5.1 Radius Scale
- shell > panel > nested > control > compact
- 겹치는 부모/자식 surface에서 자식이 부모보다 더 크게 둥글어 보이면 안 된다.

### 5.2 Field Policy
- `input/select/textarea/button`는 같은 control family로 관리한다.
- 높이, 좌우 패딩, hover, focus, border tone을 공통 토큰으로 맞춘다.

### 5.3 Layout Policy
- 좌측은 "현재 상태", 우측은 "실제 액션"으로 나눈다.
- sticky rail은 조종석, main area는 작업면으로 본다.
- 카드가 아니라 정보 블록과 panel 계층으로 읽히게 한다.

## 6. Approval UX Policy
- approval은 runtime completion과 같은 레벨의 핵심 정보다.
- pending approval은 눈에 띄어야 하지만, 무조건 큰 경고판처럼 보일 필요는 없다.
- operator가 알아야 하는 것은:
  - 왜 approval이 필요한가
  - 어떤 task에 묶여 있는가
  - 누가 처리해야 하는가
  - approve/reject 이후 어떤 결과가 나는가

## 7. Planner UX Policy
- planner provenance는 개발자 전용 디버깅 정보가 아니다.
- 상위 agent 시대에는 "왜 이 도구가 선택됐는가"가 operator에게 핵심이다.
- 최소 노출 항목:
  - planner source
  - degraded mode 여부
  - planned tools
  - executed tools
  - fallback reason

## 8. What the Dashboard Must Not Become
- 다기능 업무 앱
- 메인 채팅 인터페이스
- 모든 admin 기능의 무차별 노출면
- tool registry 편집기를 전면에 내세운 config UI
- 별도 human interactive TUI의 웹 버전

## 9. Recommended UI Split
### 9.1 Quickstart
- 목적: requester가 빠르게 요청하고 결과를 확인
- 집중: submit, current task, planner summary, approval summary, report preview

### 9.2 Console
- 목적: operator가 상태/승인/감사를 관리
- 집중: task telemetry, approval queue, approval detail, recent history, governance controls

## 10. Implementation Follow-ups
1. approval/review/admin control의 role-based visual gating 강화
2. dashboard copy 전반에서 internal jargon 제거
3. capability/readiness summary를 dashboard 상단에 추가
4. audit/report/export entry를 operator flow에 맞게 정리
5. chat panel이 들어오면 submit/status/report 보조 흐름으로만 제한
