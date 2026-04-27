# Implement Notes

## Changed Files
- `NESTCLAW_CAPABILITY_PACK_SPEC_2026-04-28.md`: defined the Stage 12 Capability Pack vocabulary, allowlist rules, approval requirements, data boundary, runtime invariants, and registry expectations.
- `configs/capability_packs.json`: added all pack ids referenced by Agent Profiles and Job Templates.
- `configs/agent_profiles.json`: expanded `allowed_capability_packs` so selected profiles can satisfy their allowed Job Templates.
- `tests/test_stage12_contract.py`: added capability pack cross-reference coverage for profiles, jobs, tool registry ids, approval policy, and runtime read-only packs.
- `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE.md`, `NESTCLAW_CAPABILITY_MANIFEST.md`, `NESTCLAW_LOCAL_LLM_JOB_CONTROL_PLANE_ROADMAP_2026-04-27.md`, `NEXT_WORK_GROUPS_2026-04-27_STAGE12.md`, `README.md`: linked Capability Pack baseline artifacts.
- `work/priority_campaigns/stage12-priority-campaign/campaign.json`: moved G3 to `in_progress`.
- `work/micro_units/stage12-w1-003/*`: initialized and advanced the G3 micro work unit.

## Rollback Plan
- Revert `NESTCLAW_CAPABILITY_PACK_SPEC_2026-04-28.md` and `configs/capability_packs.json`.
- Revert `configs/agent_profiles.json` pack expansions if Capability Pack vocabulary changes.
- Revert the Stage12 contract test additions for capability packs.
- Reset `g3-capability-pack-binding` in the campaign to `pending` and remove `stage12-w1-003` if G3 is paused.

## Known Risks
- Capability packs are still contract data, not runtime-enforced policy.
- Some readonly packs rely on runtime read surfaces rather than tool registry entries; G4 must preserve that distinction in invocation evidence.
- `ticket_draft_ops` references write-capable Redmine tools and therefore must remain dry-run or approver-gated until runtime enforcement exists.
