# NestClaw

## Status
- Deep dive in progress
- Current recommendation: position NestClaw as an organizational AI orchestration control plane, not as a general-purpose agent marketplace or agent collection

## Reference Docs
- `deep-dive-panel-report.md`
- `../../../README.md`
- `../../../NESTCLAW_AGENT_INTEGRATION_SPEC.md`
- `../../../NESTCLAW_CAPABILITY_MANIFEST.md`
- `../../../NESTCLAW_OPERATOR_DASHBOARD_PRINCIPLES.md`
- `../../../AGENT_TOOL_SURFACE_DIRECTION_2026-03-12.md`

## One-line Description
- NestClaw is an organizational orchestration backend that upper agents call, with human approval and audit dashboards on top.

## Why It Matters
- If NestClaw is framed incorrectly as an "agent collection" or "AI service hub", the product will accumulate the wrong roadmap: more UI, more personas, more catalog exposure, and weaker governance boundaries.
- If it is framed correctly as a control plane, the roadmap becomes clearer: stronger contracts, approval policy, auditability, curated capabilities, and upper-agent integration.

## Core Problem
- The codebase is increasingly consistent with `orchestration backend + human dashboard`, but some docs and posture language still describe NestClaw like an `AI-first orchestration agent`.
- That mixed framing can confuse product decisions, operator expectations, and governance policy.

## Recommended Scope
- Primary identity: organizational AI orchestration control plane
- Primary surfaces: HTTP, MCP, non-interactive CLI
- Human GUI: operator dashboard for approval, audit, and status interpretation
- Tooling posture: curated capability registry, not open marketplace sprawl
- Upper agents: first-class callers, not peers competing with NestClaw GUI

## Non-goals or Cautions
- Do not grow a separate human interactive TUI as a primary product surface.
- Do not market the tool catalog as a broad agent marketplace.
- Do not turn dashboard chat into a policy-bypassing execution surface.
- Do not let product copy imply broad autonomous multi-agent capability that the runtime does not yet support.

## Next Step
- Freeze product definition and governance language in a dedicated positioning/governance document before adding more surfaces.
