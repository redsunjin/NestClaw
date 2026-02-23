# Secure Agent Collaboration Architecture (Concept Validation)

## 질문 요약
목표:
- OpenClaw 틈새시장(업무형/비감시형) 타깃
- Local LLM + API LLM 혼용
- 에이전트 간 직접 간섭 대신 "읽기 기반 협업"으로 보안/안정성 확보 가능 여부

결론:
- **가능한 아이디어다.**
- 단, "서로의 폴더를 자유롭게 읽기"는 데이터 유출 위험이 있으므로
  **읽기 범위를 통제한 공유 채널 방식**으로 바꿔야 안전하다.

## 핵심 원칙
1. 에이전트별 private workspace 분리
- 각 에이전트는 자기 폴더에만 write 가능

2. 공용 소통 채널은 제한된 read-only 영역으로 분리
- 예: `channels/<topic>/inbox`, `channels/<topic>/outbox`
- 개인/민감 폴더 직접 read 금지

3. 중재자(Broker) 패턴 적용
- Agent A 결과 -> Broker 검증/필터링 -> Agent B 전달
- 민감정보 마스킹/정책 검증 후 전달

4. 모델 라우팅은 정책 기반
- 로컬 LLM: 민감/내부 데이터 처리
- API LLM: 공개 가능/저위험 작업

5. 모든 읽기/쓰기/전송은 감사 로그 기록
- 누가, 무엇을, 왜, 어디서 읽고 썼는지 추적

## 권장 폴더 구조
```text
workspace/
  agents/
    planner/          # planner private (rw for planner only)
    executor/         # executor private
    reviewer/         # reviewer private
  channels/
    task_<id>/
      broker_inbox/   # agents write -> broker reads
      broker_outbox/  # broker writes -> agents read
  policies/
    access_policy.yaml
    model_routing.yaml
  logs/
    audit/
```

## 접근 제어 모델 (최소)
- `planner`
  - write: `agents/planner/**`, `channels/*/broker_inbox/**`
  - read: `channels/*/broker_outbox/**`
- `executor`, `reviewer`도 동일 패턴
- `broker`
  - read/write: `channels/**`
  - read: `policies/**`

중요:
- Agent 간 private 폴더 direct read 금지
- cross-folder read는 broker_outbox 같은 "공유 채널"만 허용

## LLM 등록/라우팅 아이디어
### local llm registry
- provider: ollama, vllm, llama.cpp
- 용도: 민감 데이터, 내부 문서 분석, 오프라인 우선

### api llm registry
- provider: OpenAI/Anthropic/기타 API
- 용도: 일반 요약, 공개 자료 기반 고난도 생성

### 라우팅 규칙 예시
- sensitivity = high -> local llm only
- sensitivity = low + creativity needed -> api llm allowed
- external_send_required -> human approval mandatory

## 왜 "읽기 기반 협업"만으로는 부족한가
- read 권한도 데이터 유출 경로다.
- 따라서 "읽을 수 있다" 자체를 최소화해야 한다.
- 정답은:
  - unrestricted read가 아니라
  - broker-mediated shared-read(제한된 읽기)

## 안정성 관점 체크리스트
- [ ] 작업 단위 격리(task-scoped channel)
- [ ] 재시도/승인 전환 상태머신
- [ ] 모델 fallback(local -> api 또는 반대)
- [ ] timeout/circuit-breaker
- [ ] 감사 로그 + 리플레이 가능성

## 최종 판단
- 아이디어 자체는 유효하고 시장 방향에도 맞다.
- 보안적으로 안전하려면 아래를 강제해야 한다:
  - private workspace 격리
  - broker 중재
  - 제한된 공유 읽기
  - 정책 기반 모델 라우팅
  - 승인/감사 로그
