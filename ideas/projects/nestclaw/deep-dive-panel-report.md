# NestClaw Deep Dive Panel Report

## Panel
- Product strategy lens
- Operations and architecture lens
- Governance and risk lens

## Clarify
- NestClaw의 원래 목적은 "회사 조직을 위한 orchestration"이다.
- 현재 구현의 canonical source는 이미 이 방향에 가깝다.
  - `product_posture = orchestration_backend_with_human_dashboard` in `app/services/capability_manifest_service.py`
  - `agent.submit/status/events` is the primary entrypoint in `NESTCLAW_CAPABILITY_MANIFEST.md`
  - `dashboard` is explicitly a supervisor/operator surface in `NESTCLAW_AGENT_INTEGRATION_SPEC.md`
- 하지만 일부 문구와 로드맵 표현은 NestClaw를 `AI-first orchestration agent`나 더 넓은 agent product처럼 읽히게 만든다.
- 따라서 현재 핵심 문제는 기능 정의 부족보다 제품 정체성의 drift다.

## Design
### Recommended Product Definition
- NestClaw should be defined as an organizational AI orchestration control plane.
- More concretely:
  - upper conversational agents, scripts, and clients call NestClaw through HTTP, MCP, or CLI
  - NestClaw performs planning, policy checks, approval routing, audit logging, execution dispatch, and reporting
  - human operators use the dashboard for approval, audit, and operational supervision

### Why This Definition Fits the Current Code
- The runtime centers on orchestration contracts and policy:
  - workflow routing and request normalization in `app/services/orchestration_service.py`
  - approval gate and resume flow in `app/services/approval_service.py`
  - capability/role boundary export in `app/services/capability_manifest_service.py`
- The GUI is already being constrained into an operator surface:
  - `/console` exposes readiness, approval, recent tasks, and governance controls
  - product docs explicitly reject a separate human interactive TUI
- The tool surface is curated, not broad:
  - current planner tool set is still summary/ticket/slack centered
  - this is not yet a general agent ecosystem

### Product Wording to Prefer
- "조직용 AI orchestration control plane"
- "상위 에이전트가 호출하는 orchestration backend"
- "인간 승인/감사용 operator dashboard"

### Product Wording to Avoid
- "에이전트 모음"
- "범용 AI agent hub"
- "메인 채팅 인터페이스"
- "툴 마켓플레이스"

## Attack
### Drift Risk 1. Wrong Product Expectations
- `README.md` still uses `AI-first orchestration agent` language.
- That wording implies a more autonomous and broader product than the runtime currently supports.
- Result:
  - stakeholders expect richer autonomous multi-agent behavior
  - roadmap pressure shifts toward chat UX, more agents, more surfaces
  - governance hardening gets deprioritized

### Drift Risk 2. Dashboard Becoming the Product
- If the dashboard keeps absorbing chat, catalog, draft, and admin actions without strict role gating, it can start to look like the main app rather than the operator surface.
- This weakens the intended hierarchy:
  - upper agent is the main interaction layer
  - NestClaw is the execution/governance layer
  - dashboard is the human supervision layer

### Drift Risk 3. Curated Registry Becoming Hub Semantics
- Tool catalog, drafts, apply, rollback, and MCP exposure are useful for governance.
- But if described casually, these can be interpreted as a general marketplace or open ecosystem.
- For organizational deployments, that is dangerous because the real value is curated control, not broad extensibility without review.

### Drift Risk 4. Governance Boundary Erosion
- If NestClaw is treated like a hub of semi-autonomous agents, pressure will rise to:
  - automate approval
  - widen admin surfaces
  - normalize live mode shortcuts
  - let chat or upper agents directly mutate tool registry
- That would directly conflict with the current role and approval design.

## Validate
### What Is Strong Today
- Clear primary entrypoint: `agent.submit/status/events`
- Clear role model: requester/reviewer/approver/admin
- Clear operator posture for dashboard docs
- Clear capability manifest with machine-readable role and readiness boundaries
- Approval and audit are first-class, not bolt-ons

### What Is Still Mixed
- Product language across docs is not fully aligned
- Some roadmap and README text still carries "agent" framing where "control plane" would be more precise
- Web console still contains governance controls that can visually overstate GUI centrality

### Service Expansion and Performance Implications
- If NestClaw becomes a generic hub:
  - capability discovery, approval routing, and catalog governance become combinatorially more complex
  - the operator dashboard becomes overloaded
  - role isolation and audit consistency get harder
- If NestClaw stays a control plane:
  - surfaces can remain thin and stable
  - curated tools can expand gradually
  - governance and readiness logic stay comprehensible

## Decide
### Final Evaluation
- NestClaw should not be repositioned as an "agent collection".
- It also should not be marketed as a broad "AI service hub" unless "hub" is explicitly constrained to governed orchestration.
- The best framing is:
  - organizational AI orchestration control plane
  - with upper-agent integration as the primary usage pattern
  - and a human approval/audit dashboard as the secondary surface

### Manager / Planner Decision
1. Freeze the canonical product posture around `backend + governance + dashboard`.
2. Treat upper-agent integration as the default product story.
3. Keep the tool registry curated and policy-first.
4. Reject roadmap items that create a second primary human interaction surface.
5. Require every new surface proposal to answer:
   - does this strengthen control-plane clarity?
   - does this preserve approval/audit boundaries?
   - does this reduce or increase product identity drift?

### Immediate Follow-up Documents Recommended
- `NESTCLAW_PRODUCT_POSITIONING.md`
  - canonical product identity, target users, anti-goals
- `NESTCLAW_GOVERNANCE_GUARDRAILS.md`
  - forbidden shortcuts, approval rules, live-mode rules, tool-registry change rules
- `NESTCLAW_SURFACE_DECISION_CHECKLIST.md`
  - every new UI/CLI/MCP/chat surface must justify its role against the control-plane model
