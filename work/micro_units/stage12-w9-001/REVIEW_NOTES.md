# Review Notes

## Security / Policy Review
- Local LLM profiles require external sends to be denied and network access disabled.
- Cloud/API profiles reject unsafe sensitivity values and require redaction plus approval.
- Tool writes and external sends remain approval-bound through capability packs.

## Architecture / Workflow Review
- The validator is standalone and avoids a PyYAML runtime dependency.
- It checks registry cross-links without changing runtime behavior.
- It is wired as a required Stage 12 static gate before optional runtime smoke tests.

## QA Gate Review
- Validator must return non-zero on policy errors.
- Current intentional future registry references should be warnings, not errors.
- Stage 12 cycle must report the validator as a PASS.

## Review Verdict
- Approved as the correct next step after the harness configuration guide.
