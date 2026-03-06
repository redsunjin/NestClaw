# Plan Notes

## Scope
- Incident runtime에 `mcp-live` 실행 모드를 추가해 RAG는 dry-run, MCP만 live로 실행할 수 있게 한다.
- `app/incident_mcp.py`에 env-gated live HTTP bridge를 추가해 Redmine MCP sandbox endpoint로 요청을 보낼 수 있게 한다.
- Stage 8 live rehearsal 실행 스크립트와 운영 runbook을 추가해 실제 sandbox 검증 절차와 필요한 환경값을 고정한다.
- 정적/단위 테스트와 Stage 8 계약 테스트를 갱신해 새 자산과 live mode 분기 규칙을 고정한다.

## Out of Scope
- 실제 외부 sandbox credential 발급/보관 자동화
- 업무 지식 RAG, 시스템 분석 RAG의 live provider 연동
- 다중 ITSM(Jira, ServiceNow) 지원
- 파일럿 서비스 선정 및 Go/No-Go 의사결정 문서화

## Acceptance Criteria
- `RunIncidentRequest.run_mode`가 `dry-run`, `mcp-live`, `live`를 구분하고, `mcp-live`는 RAG dry-run + MCP live 조합으로 동작한다.
- `app/incident_mcp.py` live mode는 `NEWCLAW_REDMINE_MCP_ENDPOINT` 기반 HTTP bridge를 사용하고, 미설정 시 명시적으로 실패한다.
- `scripts/run_stage8_live_rehearsal.sh`가 live env가 없으면 `SKIP(10)` 리포트를 남기고, env가 있으면 incident create flow와 Redmine lifecycle 호출을 시도한다.
- Stage 8 live rehearsal runbook 문서가 추가되고, 필요한 env/롤백/증적 경로가 명시된다.
- `python3 -m unittest tests.test_stage8_contract tests.test_incident_adapter_contract tests.test_incident_runtime_smoke`가 통과한다.
- `bash scripts/run_micro_cycle.sh run stage8-w5-001 8`가 통과한다.

## Risks
- live MCP endpoint 계약이 실제 sandbox shim과 다르면 rehearsal script가 추가 조정이 필요할 수 있다.
- 네트워크 제한 또는 credential 부재로 실제 live rehearsal은 현재 환경에서 `SKIP`될 가능성이 높다.
- `mcp-live` 분리 중 기본 dry-run 동작을 깨면 기존 Stage 8 회귀가 발생할 수 있다.
- live response에 ticket identifier가 없으면 lifecycle 후속 호출 범위가 제한될 수 있다.

## Test Plan
- 정적/단위:
  - `python3 -m unittest tests.test_stage8_contract tests.test_incident_adapter_contract`
  - `python3 -m unittest tests.test_incident_runtime_smoke`
- 스크립트:
  - `bash scripts/run_stage8_live_rehearsal.sh` (env 미충족 시 `SKIP` expected)
- 품질게이트:
  - `bash scripts/run_dev_qa_cycle.sh 8`
  - `bash scripts/run_micro_cycle.sh run stage8-w5-001 8`
