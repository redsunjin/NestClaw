# Review Notes

## Security / Policy Review
- validation report에는 spec summary와 check 결과만 남기고 raw credential 같은 민감정보는 허용하지 않는다.
- rollback과 apply는 기존대로 `approver/admin`만 가능해야 하며 `acted_by`와 인증 actor를 일치시켜야 한다.
- maintenance script는 overlay file을 직접 수정하므로 validate 후 compact 순서를 지키고 실패 시 non-zero exit로 멈춰야 한다.

## Architecture / Workflow Review
- validation logic은 `app/tool_registry.py` 수준의 deterministic utility로 두고, API/CLI/MCP는 같은 결과를 재사용하는 편이 맞다.
- rollback은 overlay history snapshot을 기준으로 restore/remove를 수행해야 하며, base registry는 직접 수정하지 않는 것이 맞다.
- maintenance script는 runtime service 바깥의 운영 보조 계층으로 두되 tool registry utility를 재사용해야 한다.

## QA Gate Review
- runtime tests에서 draft create -> validate -> apply -> rollback 흐름을 실제 API로 검증해야 한다.
- CLI smoke와 MCP smoke에 validation/rollback 명령을 추가해 surface 일관성을 확인해야 한다.
- contract tests는 maintenance script, validation utility, rollback utility 존재를 고정해야 한다.

## Review Verdict
- 진행 승인.
- 이번 단계는 runtime overlay governance hardening에 집중하고 GUI 작업은 후속으로 미룬다.
