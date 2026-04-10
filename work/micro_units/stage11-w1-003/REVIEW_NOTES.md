# Review Notes

## Security / Policy Review
- deployment profile은 실행 편의 문서가 아니라 trust boundary 문서이기도 하므로, `requester/reviewer` 기본값과 `approver/admin` elevated 경계를 같이 써야 한다.
- upper-agent host profile이 packaged remote gateway처럼 오해되면 안 된다. 현재 baseline은 `stdio child process`이고, remote exposure는 future boundary로 계속 남겨야 한다.
- bootstrap artifact에는 secret 값을 담지 않고, auth mode와 actor context 주입 책임만 명시하는 편이 맞다.

## Architecture / Workflow Review
- profile은 기존 HTTP + MCP transport를 반복 가능한 배치 형태로 묶는 것이어야 하고, 새로운 실행 엔진을 추가하면 안 된다.
- local dev, operator sidecar, upper-agent host 세 프로필은 공통 baseline을 유지하되 `reload 여부`, `http required 여부`, `actor context source` 차이만 최소한으로 드러내는 편이 적절하다.
- 문서와 artifact가 따로 놀지 않게 machine-readable profile과 human guide를 같이 두고, validator smoke가 둘의 drift를 막아야 한다.

## QA Gate Review
- Stage 11 contract는 bootstrap guide, profile artifact, validator smoke, current MWU state를 함께 고정해야 한다.
- `bash scripts/run_dev_qa_cycle.sh 11`에 stage11 deployment profile smoke를 추가해 새 profile이 회귀 없이 유지되는지 확인해야 한다.
- env-gated skip 외 신규 failure가 없어야 하고, bootstrap profile validator는 로컬 env 유무와 무관하게 PASS해야 한다.

## Review Verdict
- 진행 승인.
- 이번 단계는 canonical bootstrap guide, machine-readable deployment profile, lightweight validator, contract/smoke hardening 범위로 제한한다.
