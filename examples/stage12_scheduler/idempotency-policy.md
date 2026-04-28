# Stage 12 Scheduler Idempotency Examples

Use explicit business idempotency keys for scheduled jobs. The derived fingerprint key is acceptable for ad hoc manual runs, but external schedulers should pass a stable key for the intended run bucket.

| Template | Key Format | Example | Recommended Duplicate Policy |
| --- | --- | --- | --- |
| `daily_status_digest` | `stage12:{template_id}:daily:{date}:{audience}` | `stage12:daily_status_digest:daily:2026-04-28:ops_team` | `skip` |
| `issue_triage` | `stage12:{template_id}:issue:{source_system}:{issue_id}:{event_batch}` | `stage12:issue_triage:issue:redmine:NC-1024:2026-04-28T09` | `fail` |
| `readiness_check` | `stage12:{template_id}:readiness:{check_set}:stage{target_stage}:{env_profile}:{schedule_bucket}` | `stage12:readiness_check:readiness:stage12-scheduler-smoke:stage12:local:2026-04-28` | `skip` |

Operational rule: do not include `profile_id` in explicit scheduled keys. A scheduled business run should dedupe even if the operator later routes it through another allowed profile.
