# IdP Key Rotation Rehearsal Runbook

## 목적
실제 운영 키 교체 전, 토큰 검증 경로에서
- 이전 키 토큰 차단
- 신규 키 토큰 허용
이 정확히 동작하는지 검증한다.

## 담당 전문가
- A04 Security Privacy: 키 교체 정책/검증 책임
- A06 QA Reliability: 리허설 증적/회귀 검증 책임
- A02 Workflow Engineer: 실행 스크립트/환경 안정성 책임
- A01 Product Owner: 운영 승인/중단 의사결정

## 사전 조건
1. Python 런타임과 `fastapi` 의존성 설치
2. JWKS 파일 접근 가능
3. 교체 전(old) 토큰과 교체 후(new) 토큰 확보
4. 테스트 환경에서 먼저 실행

## 필수 환경변수
```bash
export NEWCLAW_IDP_REHEARSAL_JWKS_PATH="/path/to/jwks.json"
export NEWCLAW_IDP_REHEARSAL_ISSUER="https://idp.example"
export NEWCLAW_IDP_REHEARSAL_AUDIENCE="new_claw"
export NEWCLAW_IDP_REHEARSAL_OLD_TOKEN="<old_jwt>"
export NEWCLAW_IDP_REHEARSAL_NEW_TOKEN="<new_jwt>"
```

## 실행
```bash
bash scripts/run_idp_key_rotation_rehearsal.sh
```

## 판정 기준
- PASS:
  - `tests.test_auth_idp` 통과
  - old token: 401로 거절
  - new token: 정상 허용
- FAIL:
  - old token 허용됨
  - new token 거절됨
  - 단위테스트 실패

## 산출물
- 리포트 파일: `reports/qa/idp-rotation-rehearsal-<timestamp>.md`
- 운영 승인 시 첨부 항목:
  - 실행 시각(UTC)
  - 사용한 JWKS 경로/issuer/audience
  - old/new 토큰 판정 결과

## 롤백 기준
아래 중 하나라도 발생하면 즉시 롤백:
1. 신규 토큰 인증 실패
2. 이전 토큰 인증 성공
3. 인증 오류율 급증

## 롤백 절차
1. 이전 JWKS(혹은 key set)로 즉시 복원
2. `scripts/run_idp_key_rotation_rehearsal.sh` 재실행
3. PASS 확인 후 재배포 여부 재결정
