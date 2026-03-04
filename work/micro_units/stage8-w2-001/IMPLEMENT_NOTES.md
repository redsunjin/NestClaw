# Implement Notes

## Changed Files
- [x] `app/incident_rag.py`
  - Stage 8 RAG adapter contract skeleton 구현
  - `fetch_knowledge_evidence`, `fetch_system_signals` dry-run 반환 지원
- [x] `app/incident_mcp.py`
  - Stage 8 MCP adapter contract skeleton 구현
  - `execute_redmine_action`, 민감정보 마스킹 함수 구현
- [x] `app/main.py`
  - Stage 8 adapter registry 연결(초기 import/contract binding point)
- [x] `tests/test_incident_adapter_contract.py`
  - 어댑터 시그니처/계약/마스킹 동작 정적 테스트 추가
- [x] `scripts/run_dev_qa_cycle.sh`
  - Stage 8 게이트에 incident adapter contract 테스트 추가
- [x] `scripts/run_doc_audit.sh`
  - Stage 8 adapter 파일/마이크로 유닛 계획 감사 규칙 추가
- [x] `tests/test_stage8_contract.py`
  - Stage 8 자산 검증 범위에 adapter 파일/테스트 포함

## Rollback Plan
- `git revert <this-commit>`으로 단일 커밋 롤백
- 부분 롤백 필요 시 아래 파일만 복원:
  - `app/incident_rag.py`
  - `app/incident_mcp.py`
  - `app/main.py`
  - `tests/test_incident_adapter_contract.py`
  - `scripts/run_dev_qa_cycle.sh`
  - `scripts/run_doc_audit.sh`
  - `tests/test_stage8_contract.py`
- 롤백 후 확인:
  - `python3 -m unittest tests.test_spec_contract`
  - `bash scripts/run_dev_qa_cycle.sh 8`

## Known Risks
- 현재는 dry-run 전용 구현이며 live 호출은 미구현이다.
- `app/main.py`는 registry까지만 연결되어 incident runtime 경로는 아직 비활성 상태다.
- Stage 8 runtime smoke(`fastapi` 의존)는 환경 미충족 시 SKIP될 수 있다.
