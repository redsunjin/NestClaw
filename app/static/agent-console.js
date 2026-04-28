const actorIdInput = document.querySelector("#actor-id");
const actorRoleSelect = document.querySelector("#actor-role");
const actedByInput = document.querySelector("#acted-by");
const agentTaskKindSelect = document.querySelector("#agent-task-kind");
const agentTitleInput = document.querySelector("#agent-title");
const agentRunModeSelect = document.querySelector("#agent-run-mode");
const agentRequestTextInput = document.querySelector("#agent-request-text");
const agentMetadataInput = document.querySelector("#agent-metadata");
const agentTaskIdInput = document.querySelector("#agent-task-id");
const agentResolvedKindInput = document.querySelector("#agent-resolved-kind");
const agentStatusInput = document.querySelector("#agent-status");
const agentSummary = document.querySelector("#agent-summary");
const plannerSummary = document.querySelector("#planner-summary");
const plannerSignalStrip = document.querySelector("#planner-signal-strip");
const plannerRationale = document.querySelector("#planner-rationale");
const planDetail = document.querySelector("#plan-detail");
const executionDetail = document.querySelector("#execution-detail");
const reportPreview = document.querySelector("#report-preview");
const recentTaskList = document.querySelector("#recent-task-list");
const recentApprovalList = document.querySelector("#recent-approval-list");
const jobRunList = document.querySelector("#job-run-list");
const jobHistoryTemplateSelect = document.querySelector("#job-history-template");
const harnessSummary = document.querySelector("#harness-summary");
const harnessProfileList = document.querySelector("#harness-profile-list");
const approvalStatusFilterSelect = document.querySelector("#approval-status-filter");
const approvalGroupFilterInput = document.querySelector("#approval-group-filter");
const approvalCommentInput = document.querySelector("#approval-comment");
const approvalDetailIdInput = document.querySelector("#approval-detail-id");
const filterFamilyInput = document.querySelector("#filter-family");
const filterSystemInput = document.querySelector("#filter-system");
const draftRequestTextInput = document.querySelector("#draft-request-text");
const draftToolIdInput = document.querySelector("#draft-tool-id");
const draftTitleInput = document.querySelector("#draft-title");
const draftIdInput = document.querySelector("#draft-id");
const output = document.querySelector("#output");
const toolList = document.querySelector("#tool-list");
const approvalList = document.querySelector("#approval-list");
const approvalDetail = document.querySelector("#approval-detail");
const healthBadge = document.querySelector("#health-badge");
const readinessBadge = document.querySelector("#readiness-badge");
const capabilitySummary = document.querySelector("#capability-summary");
const roleModeSummary = document.querySelector("#role-mode-summary");
const actorModeNote = document.querySelector("#actor-mode-note");
const runModeNote = document.querySelector("#run-mode-note");
const roleScopedElements = [...document.querySelectorAll("[data-role-scope]")];
let currentTaskId = "";
let currentApprovalQueueId = "";

function headers() {
  return {
    "Content-Type": "application/json",
    "X-Actor-Id": actorIdInput.value.trim() || "qa_user",
    "X-Actor-Role": actorRoleSelect.value,
  };
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...headers(),
      ...(options.headers || {}),
    },
  });
  const text = await response.text();
  let payload;
  try {
    payload = text ? JSON.parse(text) : {};
  } catch (_error) {
    payload = { raw: text };
  }
  if (!response.ok) {
    throw new Error(JSON.stringify(payload, null, 2));
  }
  return payload;
}

function printOutput(title, payload) {
  output.textContent = `${title}\n\n${JSON.stringify(payload, null, 2)}`;
}

function isElevatedRole(role = actorRoleSelect.value) {
  return ["approver", "admin"].includes(role);
}

function roleProfile(role = actorRoleSelect.value) {
  if (role === "admin") {
    return {
      summary: "admin은 승인, registry governance, live 성격 제어까지 포함한 운영 제어면을 봅니다.",
      actorNote: "admin은 승인 처리와 draft 적용을 직접 수행할 수 있습니다.",
      runModeNote: "admin은 dry-run 외 run mode도 검토할 수 있지만, live는 운영 기준 아래에서만 써야 합니다.",
    };
  }
  if (role === "approver") {
    return {
      summary: "approver는 승인 큐와 승인 이력, draft 적용 같은 운영 제어면을 봅니다.",
      actorNote: "approver는 승인 처리와 draft 적용을 수행할 수 있습니다.",
      runModeNote: "approver는 필요한 경우 live 성격 run mode를 검토할 수 있습니다.",
    };
  }
  if (role === "reviewer") {
    return {
      summary: "reviewer는 planner와 실행 결과를 읽고 검토하지만, 승인과 적용 제어는 보지 않습니다.",
      actorNote: "reviewer는 상태와 planner rationale을 읽는 역할입니다. 승인과 적용 제어는 숨겨집니다.",
      runModeNote: "reviewer는 dry-run 중심으로 상태를 검토합니다. live 성격 run mode는 잠깁니다.",
    };
  }
  return {
    summary: "requester는 요청 제출과 결과 확인에 집중하고, 승인과 governance는 approver/admin이 맡습니다.",
    actorNote: "requester는 읽기 중심입니다. 승인과 registry governance는 approver/admin에서 닫습니다.",
    runModeNote: "requester는 dry-run 중심으로만 실행을 확인합니다. live 성격 run mode는 잠깁니다.",
  };
}

function applyRunModeVisibility() {
  const elevated = isElevatedRole();
  [...agentRunModeSelect.options].forEach((option) => {
    if (option.value === "dry-run") {
      option.disabled = false;
      return;
    }
    option.disabled = !elevated;
  });
  if (!elevated && agentRunModeSelect.value !== "dry-run") {
    agentRunModeSelect.value = "dry-run";
  }
}

function applyRoleVisibility() {
  const role = actorRoleSelect.value;
  roleScopedElements.forEach((element) => {
    const allowed = String(element.dataset.roleScope || "")
      .split(/\s+/)
      .filter(Boolean);
    const isVisible = !allowed.length || allowed.includes(role);
    element.classList.toggle("is-role-hidden", !isVisible);
  });
  const profile = roleProfile(role);
  roleModeSummary.textContent = profile.summary;
  actorModeNote.textContent = profile.actorNote;
  runModeNote.textContent = profile.runModeNote;
  applyRunModeVisibility();
  if (!isElevatedRole(role)) {
    approvalList.innerHTML = "";
    recentApprovalList.innerHTML = "";
    setApprovalDetail("approver/admin 역할에서만 승인 상세와 이력을 확인할 수 있습니다.");
  }
}

function setAgentSummary(lines) {
  agentSummary.textContent = Array.isArray(lines) ? lines.join("\n") : String(lines || "");
}

function setPlannerSummary(lines) {
  plannerSummary.textContent = Array.isArray(lines) ? lines.join("\n") : String(lines || "");
}

function setPlannerRationale(lines) {
  plannerRationale.textContent = Array.isArray(lines) ? lines.join("\n") : String(lines || "");
}

function setPlanDetail(content) {
  if (typeof content === "string") {
    planDetail.textContent = content;
    return;
  }
  planDetail.innerHTML = content;
}

function setExecutionDetail(content) {
  if (typeof content === "string") {
    executionDetail.textContent = content;
    return;
  }
  executionDetail.innerHTML = content;
}

function setReportPreview(lines) {
  reportPreview.textContent = Array.isArray(lines) ? lines.join("\n") : String(lines || "");
}

function setApprovalDetail(lines) {
  approvalDetail.textContent = Array.isArray(lines) ? lines.join("\n") : String(lines || "");
}

function toolFlow(items) {
  const values = (items || []).filter(Boolean);
  return values.length ? values.join(" -> ") : "-";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function plannerLabel(item) {
  const provider = item.planning_provider_id ? ` via ${item.planning_provider_id}` : "";
  const degraded = item.planning_degraded_mode ? " [degraded]" : "";
  return `${item.planning_source || "-"}${provider}${degraded}`;
}

function planningContext(payload) {
  const provenance = payload?.planning_provenance || {};
  const providerSelection = provenance.provider_selection || {};
  return {
    provenance,
    providerSelection,
    plannedActions: payload?.planned_actions || [],
    actionResults: payload?.action_results || [],
    status: payload?.status || "",
    runMode: payload?.run_mode || "",
    approvalQueueId: payload?.approval_queue_id || "",
    reportPath: (payload?.result || {}).report_path || "",
  };
}

function stateSummaryContext(payload) {
  return payload?.state_summary || {};
}

function signalChip(label, tone = "muted") {
  return `<span class="signal-chip signal-chip-${tone}">${escapeHtml(label)}</span>`;
}

function signalChips(payload) {
  const { provenance, providerSelection, status, runMode, approvalQueueId, reportPath } = planningContext(payload);
  const stateSummary = stateSummaryContext(payload);
  const chips = [
    signalChip(`planner ${provenance.source || "-"}`, provenance.source ? "ok" : "muted"),
    signalChip(
      `provider ${providerSelection.provider_id || "-"}`,
      providerSelection.provider_id ? "muted" : "muted"
    ),
    signalChip(provenance.degraded_mode ? "degraded mode" : "standard mode", provenance.degraded_mode ? "warn" : "ok"),
  ];
  if (provenance.confidence !== undefined && provenance.confidence !== null) {
    chips.push(signalChip(`confidence ${provenance.confidence}`, "muted"));
  }
  if (provenance.fallback_reason) {
    chips.push(signalChip(`fallback ${provenance.fallback_reason}`, "warn"));
  }
  if (runMode) {
    chips.push(signalChip(`run ${runMode}`, runMode === "dry-run" ? "muted" : "warn"));
  }
  if (approvalQueueId || status === "NEEDS_HUMAN_APPROVAL") {
    chips.push(signalChip("approval required", "warn"));
  }
  if (stateSummary.canonical_reason_code && !["ready", "running", "completed"].includes(stateSummary.canonical_reason_code)) {
    chips.push(signalChip(`reason ${stateSummary.canonical_reason_code}`, stateSummary.canonical_reason_code === "planner_degraded" ? "warn" : "muted"));
  }
  if (reportPath) {
    chips.push(signalChip("report ready", "ok"));
  }
  return chips;
}

function payloadSummary(payload) {
  if (!payload || typeof payload !== "object") {
    return "-";
  }
  const priorityKeys = ["subject", "service", "summary", "title", "meeting_title", "text_preview", "description"];
  for (const key of priorityKeys) {
    if (payload[key]) {
      return String(payload[key]);
    }
  }
  const keys = Object.keys(payload);
  if (!keys.length) {
    return "-";
  }
  const summary = keys
    .slice(0, 3)
    .map((key) => `${key}=${String(payload[key])}`)
    .join(" / ");
  return summary.length > 160 ? `${summary.slice(0, 157)}...` : summary;
}

function actionStepMarkup(item, index) {
  const executionCall = item.execution_call || {};
  const adapter = executionCall.adapter || item.adapter || "-";
  const method = executionCall.method || item.method || "-";
  const reason = item.reason || "";
  const requestPayload = executionCall.payload || item.request_payload || {};
  const payloadNote = payloadSummary(requestPayload);
  return `
    <article class="action-step">
      <div class="step-index">${index + 1}</div>
      <div class="step-body">
        <p class="step-title">${escapeHtml(item.tool_id || "-")}</p>
        <p class="step-meta">${escapeHtml(adapter)} / ${escapeHtml(method)}</p>
        ${reason ? `<p class="step-note">${escapeHtml(reason)}</p>` : ""}
        ${payloadNote && payloadNote !== "-" ? `<p class="step-note muted">${escapeHtml(payloadNote)}</p>` : ""}
      </div>
    </article>
  `;
}

function executionStepMarkup(item, index) {
  const status = item.status || item.mode || "-";
  const payloadNote = payloadSummary(item.request_payload || {});
  return `
    <article class="action-step execution-step">
      <div class="step-index">${index + 1}</div>
      <div class="step-body">
        <p class="step-title">${escapeHtml(item.tool_id || "-")}</p>
        <p class="step-meta">${escapeHtml(item.adapter || "-")} / ${escapeHtml(item.method || "-")}</p>
        <p class="step-note">${escapeHtml(status)}${item.mode ? ` · ${escapeHtml(item.mode)}` : ""}</p>
        ${payloadNote && payloadNote !== "-" ? `<p class="step-note muted">${escapeHtml(payloadNote)}</p>` : ""}
      </div>
    </article>
  `;
}

function renderSignalStrip(payload) {
  plannerSignalStrip.innerHTML = signalChips(payload).join("");
}

function renderActionInspector(element, items, builder, emptyText) {
  if (!(items || []).length) {
    element.textContent = emptyText;
    return;
  }
  element.innerHTML = `<div class="action-rail">${items.map(builder).join("")}</div>`;
}

function plannerSummaryLines(payload) {
  const { provenance, providerSelection, plannedActions, actionResults } = planningContext(payload);
  const stateSummary = stateSummaryContext(payload);
  const plannedTools = plannedActions.map((item) => item.tool_id).filter(Boolean);
  const executedTools = actionResults.map((item) => item.tool_id).filter(Boolean);
  return [
    `canonical_state: ${stateSummary.canonical_state || "-"}`,
    `canonical_reason: ${stateSummary.canonical_reason_code || "-"}`,
    stateSummary.detail_reason_code ? `detail_reason: ${stateSummary.detail_reason_code}` : "",
    `planner_source: ${provenance.source || "-"}`,
    `provider: ${providerSelection.provider_id || "-"}`,
    `degraded_mode: ${provenance.degraded_mode ? "yes" : "no"}`,
    provenance.confidence !== undefined && provenance.confidence !== null ? `confidence: ${provenance.confidence}` : "",
    provenance.fallback_reason ? `fallback_reason: ${provenance.fallback_reason}` : "",
    `planned_tools: ${toolFlow(plannedTools)}`,
    executedTools.length ? `executed_tools: ${toolFlow(executedTools)}` : "",
  ].filter(Boolean);
}

function capabilitySummaryLines(payload) {
  const families = (payload?.workflow_families || [])
    .map((item) => `${item.kind}: ${item.status}`)
    .join("\n");
  const toolCount = payload?.tool_catalog?.count ?? "-";
  const readiness = payload?.readiness?.stage8_live_readiness || {};
  const missing = (readiness.missing_env || []).slice(0, 2);
  return [
    `entrypoint: ${payload?.primary_entrypoint || "-"}`,
    families ? `families: ${families}` : "",
    `tool_count: ${toolCount}`,
    `live_readiness: ${readiness.status || "-"}`,
    `readiness_reason: ${readiness.canonical_reason_code || "-"}`,
    readiness.detail_reason_code ? `readiness_detail: ${readiness.detail_reason_code}` : "",
    missing.length ? `missing_env: ${missing.join(", ")}` : "",
  ].filter(Boolean);
}

function rationaleLines(payload) {
  const { provenance } = planningContext(payload);
  return [
    provenance.rationale ? `rationale: ${provenance.rationale}` : "아직 planner rationale이 없습니다.",
    provenance.fallback_reason ? `fallback_reason: ${provenance.fallback_reason}` : "",
  ].filter(Boolean);
}

function parseMetadataInput() {
  const raw = agentMetadataInput.value.trim();
  if (!raw) {
    return {};
  }
  return JSON.parse(raw);
}

function fillAgentExample(kind) {
  if (kind === "incident") {
    agentTaskKindSelect.value = "auto";
    agentTitleInput.value = "billing-api 장애 대응";
    agentRunModeSelect.value = "dry-run";
    agentRequestTextInput.value = "billing-api 장애 대응용 티켓을 생성하고 온콜이 볼 수 있게 정리해줘";
    agentMetadataInput.value = JSON.stringify(
      {
        service: "billing-api",
        severity: "low",
        time_window: "15m",
        notify_channel: "#ops-alerts",
      },
      null,
      2
    );
    return;
  }

  if (kind === "approval") {
    agentTaskKindSelect.value = "task";
    agentTitleInput.value = "외부 전송 승인 요청";
    agentRunModeSelect.value = "dry-run";
    agentRequestTextInput.value = "회의 내용을 정리하고 외부 전송 승인까지 올려줘";
    agentMetadataInput.value = JSON.stringify(
      {
        meeting_title: "외부 전송 검토",
        meeting_date: "2026-03-13",
        participants: ["Ops"],
        notes: "요약 결과를 외부 전송 해주세요",
      },
      null,
      2
    );
    return;
  }

  agentTaskKindSelect.value = "task";
  agentTitleInput.value = "주간 운영회의 요약";
  agentRunModeSelect.value = "dry-run";
  agentRequestTextInput.value = "주간 운영회의 메모를 요약하고 액션 아이템을 정리해줘";
  agentMetadataInput.value = JSON.stringify(
    {
      meeting_title: "주간 운영회의",
      meeting_date: "2026-03-13",
      participants: ["Kim", "Lee"],
      notes: "업무A 진행\n업무B 리스크\n업무C 일정",
    },
    null,
    2
  );
}

function renderTools(items) {
  if (!items.length) {
    toolList.innerHTML = '<div class="tool-card"><h3>도구 없음</h3><p class="tool-meta">현재 필터에 맞는 도구가 없습니다.</p></div>';
    return;
  }
  toolList.innerHTML = items
    .map(
      (item) => `
        <article class="tool-card">
          <h3>${item.tool_id}</h3>
          <p class="tool-meta">${item.title || "-"}</p>
          <p class="tool-meta">adapter: ${item.adapter}</p>
          <p class="tool-meta">method: ${item.method}</p>
          <p class="tool-meta">family/system: ${item.capability_family} / ${item.external_system}</p>
        </article>
      `
    )
    .join("");
}

function renderApprovals(items) {
  const elevated = isElevatedRole();
  if (!items.length) {
    approvalList.innerHTML = '<div class="approval-card"><h3>승인 항목 없음</h3><p class="tool-meta">현재 필터에 맞는 승인 요청이 없습니다.</p></div>';
    return;
  }
  approvalList.innerHTML = items
    .map(
      (item) => `
        <article class="approval-card">
          <h3>${item.queue_id}</h3>
          <p class="tool-meta">task: ${item.task_id}</p>
          <p class="tool-meta">reason: ${item.reason_code}</p>
          <p class="tool-meta">status: ${item.status}</p>
          <p class="tool-meta">approver_group: ${item.approver_group}</p>
          <div class="approval-actions">
            <button class="button subtle" type="button" data-approval-detail="${item.queue_id}">상세/이력</button>
            ${elevated ? `<button class="button subtle" type="button" data-approve="${item.queue_id}">Approve</button>` : ""}
            ${elevated ? `<button class="button danger" type="button" data-reject="${item.queue_id}">Reject</button>` : ""}
          </div>
        </article>
      `
    )
    .join("");
}

function renderRecentTasks(items) {
  if (!items.length) {
    recentTaskList.innerHTML = '<div class="history-card"><p class="tool-meta">최근 작업이 없습니다.</p></div>';
    return;
  }
  recentTaskList.innerHTML = items
    .map(
      (item) => `
        <article class="history-card">
          <h3>${item.task_id}</h3>
          <p class="tool-meta">${item.title || "-"}</p>
          <p class="tool-meta">kind/status: ${item.resolved_kind} / ${item.status}</p>
          <p class="tool-meta">canonical: ${(item.state_summary || {}).canonical_state || "-"} / ${(item.state_summary || {}).canonical_reason_code || "-"}</p>
          <p class="tool-meta">requested_by: ${item.requested_by}</p>
          <p class="tool-meta">planner: ${plannerLabel(item)}</p>
          <div class="signal-strip signal-strip-compact">
            ${signalChip(item.planning_degraded_mode ? "degraded" : "standard", item.planning_degraded_mode ? "warn" : "ok")}
            ${item.run_mode ? signalChip(`run ${item.run_mode}`, item.run_mode === "dry-run" ? "muted" : "warn") : ""}
            ${item.report_path ? signalChip("report ready", "ok") : ""}
          </div>
          <p class="tool-meta">${item.planning_rationale || item.planning_fallback_reason || "planner rationale 없음"}</p>
          <p class="tool-meta">planned_tools: ${toolFlow(item.planned_tool_ids || [])}</p>
          <p class="tool-meta">executed_tools: ${toolFlow(item.executed_tool_ids || [])}</p>
          <p class="tool-meta">updated_at: ${item.updated_at || "-"}</p>
          <div class="approval-actions">
            <button class="button subtle" type="button" data-load-task="${item.task_id}">불러오기</button>
            ${item.report_path ? `<button class="button subtle" type="button" data-preview-report="${item.task_id}">미리보기</button>` : ""}
            ${item.report_path ? `<button class="button subtle" type="button" data-open-report="${item.task_id}">원문 열기</button>` : ""}
          </div>
        </article>
      `
    )
    .join("");
}

function renderJobRuns(items) {
  if (!items.length) {
    jobRunList.innerHTML = '<div class="history-card"><p class="tool-meta">Stage 12 job 실행 이력이 없습니다.</p></div>';
    return;
  }
  jobRunList.innerHTML = items
    .map((item) => {
      const state = item.state_summary || {};
      const budget = item.budget_enforcement || {};
      const packs = (item.capability_pack_ids || []).join(", ") || "-";
      return `
        <article class="history-card job-run-card">
          <h3>${escapeHtml(item.template_id || "-")}</h3>
          <p class="tool-meta">task: ${escapeHtml(item.task_id || "-")}</p>
          <p class="tool-meta">status: ${escapeHtml(item.status || "-")} / ${escapeHtml(state.canonical_state || "-")}</p>
          <p class="tool-meta">profile/provider: ${escapeHtml(item.profile_id || "-")} / ${escapeHtml(item.provider_id || "-")}</p>
          <p class="tool-meta">packs: ${escapeHtml(packs)}</p>
          <p class="tool-meta">budget: ${budget.enforced ? "enforced" : "-"} · context ${budget.input_payload_bytes ?? "-"} / ${budget.max_context_bytes ?? "-"}</p>
          <div class="signal-strip signal-strip-compact">
            ${signalChip(item.resolved_kind || "-", item.resolved_kind === "incident" ? "warn" : "muted")}
            ${item.run_mode ? signalChip(`run ${item.run_mode}`, item.run_mode === "dry-run" ? "muted" : "warn") : ""}
            ${item.report_path ? signalChip("report ready", "ok") : ""}
            ${item.approval_queue_id ? signalChip("approval", "warn") : ""}
          </div>
          <p class="tool-meta">planned_tools: ${toolFlow(item.planned_tool_ids || [])}</p>
          <p class="tool-meta">executed_tools: ${toolFlow(item.executed_tool_ids || [])}</p>
          <p class="tool-meta">updated_at: ${escapeHtml(item.updated_at || "-")}</p>
          <div class="approval-actions">
            <button class="button subtle" type="button" data-load-job-task="${escapeHtml(item.task_id || "")}">상태 보기</button>
            ${item.report_path ? `<button class="button subtle" type="button" data-preview-job-report="${escapeHtml(item.task_id || "")}">보고서</button>` : ""}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderHarness(payload) {
  const counts = payload.counts || {};
  const validation = payload.validation || {};
  const onboarding = payload.onboarding || {};
  harnessSummary.textContent = [
    `status: ${payload.status || "-"}`,
    `validator: ${validation.strict_status || validation.status || "-"}`,
    `profiles: ${counts.profiles ?? "-"} (${counts.local_profiles ?? "-"} local / ${counts.cloud_profiles ?? "-"} cloud)`,
    `job_templates: ${counts.job_templates ?? "-"}`,
    `capability_packs: ${counts.capability_packs ?? "-"}`,
    `model_providers: ${counts.model_providers ?? "-"}`,
    `primary_local: ${onboarding.primary_local_profile || "-"} -> ${onboarding.primary_local_provider || "-"}`,
    `smoke: ${onboarding.smoke_script || "-"}`,
  ].join("\n");

  const profiles = payload.profiles || [];
  if (!profiles.length) {
    harnessProfileList.innerHTML = '<div class="history-card"><p class="tool-meta">등록된 harness profile이 없습니다.</p></div>';
    return;
  }
  harnessProfileList.innerHTML = profiles
    .map((profile) => {
      const jobs = (profile.allowed_job_templates || []).join(", ") || "-";
      const packs = (profile.allowed_capability_packs || []).join(", ") || "-";
      const sensitivity = (profile.allowed_sensitivity || []).join(", ") || "-";
      return `
        <article class="history-card harness-card">
          <h3>${escapeHtml(profile.profile_id || "-")}</h3>
          <p class="tool-meta">provider: ${escapeHtml(profile.provider_id || "-")} / ${escapeHtml(profile.provider_class || "-")}</p>
          <p class="tool-meta">jobs: ${escapeHtml(jobs)}</p>
          <p class="tool-meta">packs: ${escapeHtml(packs)}</p>
          <p class="tool-meta">sensitivity: ${escapeHtml(sensitivity)}</p>
          <div class="signal-strip signal-strip-compact">
            ${signalChip(profile.enabled ? "enabled" : "disabled", profile.enabled ? "ok" : "warn")}
            ${signalChip(`external ${profile.external_send_policy || "-"}`, profile.external_send_policy === "deny" ? "ok" : "warn")}
            ${signalChip(profile.allow_network ? "network allowed" : "network denied", profile.allow_network ? "warn" : "ok")}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderRecentApprovals(items) {
  if (!items.length) {
    recentApprovalList.innerHTML = '<div class="history-card"><p class="tool-meta">최근 승인 이력이 없습니다.</p></div>';
    return;
  }
  recentApprovalList.innerHTML = items
    .map(
      (item) => `
        <article class="history-card">
          <h3>${item.queue_id}</h3>
          <p class="tool-meta">task: ${item.task_id}</p>
          <p class="tool-meta">status/reason: ${item.status} / ${item.reason_code}</p>
          <p class="tool-meta">requested_by: ${item.requested_by}</p>
          <p class="tool-meta">at: ${item.resolved_at || item.created_at || "-"}</p>
          <div class="approval-actions">
            <button class="button subtle" type="button" data-approval-detail="${item.queue_id}">상세/이력</button>
          </div>
        </article>
      `
    )
    .join("");
}

async function loadHealth() {
  try {
    const payload = await requestJson("/health", { headers: { "Content-Type": "application/json" } });
    healthBadge.textContent = payload.status === "ok" ? "서버 정상" : "확인 필요";
    healthBadge.className = `badge ${payload.status === "ok" ? "ok" : "pending"}`;
  } catch (_error) {
    healthBadge.textContent = "서버 오류";
    healthBadge.className = "badge fail";
  }
}

async function loadCapabilities() {
  const payload = await requestJson("/api/v1/capabilities");
  capabilitySummary.textContent = capabilitySummaryLines(payload).join("\n");
  const readiness = payload?.readiness?.stage8_live_readiness || {};
  const isReady = readiness.status === "ready";
  readinessBadge.textContent = isReady ? "ready" : `${readiness.canonical_reason_code || "blocked"}`;
  readinessBadge.className = `badge ${isReady ? "ok" : "pending"}`;
  return payload;
}

async function loadTools() {
  const params = new URLSearchParams();
  if (filterFamilyInput.value.trim()) {
    params.set("capability_family", filterFamilyInput.value.trim());
  }
  if (filterSystemInput.value.trim()) {
    params.set("external_system", filterSystemInput.value.trim());
  }
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const payload = await requestJson(`/api/v1/tools${suffix}`);
  renderTools(payload.items || []);
  printOutput("도구 목록", payload);
}

async function loadRecentTasks() {
  const payload = await requestJson("/api/v1/agent/recent?limit=8");
  renderRecentTasks(payload.items || []);
  printOutput("최근 작업", payload);
}

async function loadJobHistory() {
  const params = new URLSearchParams();
  params.set("limit", "8");
  if (jobHistoryTemplateSelect.value) {
    params.set("template_id", jobHistoryTemplateSelect.value);
  }
  const payload = await requestJson(`/api/v1/jobs/runs?${params.toString()}`);
  renderJobRuns(payload.items || []);
  printOutput("Stage 12 Job 실행 이력", payload);
  return payload;
}

async function loadHarness() {
  const payload = await requestJson("/api/v1/llm-harness");
  renderHarness(payload);
  printOutput("LLM Harness 상태", payload);
  return payload;
}

async function loadReportPreview(taskId = currentTaskId) {
  if (!taskId) {
    printOutput("보고서 미리보기 오류", { error: "task_id를 먼저 입력하거나 최근 작업에서 선택하세요." });
    return null;
  }
  const payload = await requestJson(`/api/v1/agent/report/${taskId}?max_chars=4000`);
  setReportPreview([
    `task_id: ${payload.task_id || "-"}`,
    `resolved_kind: ${payload.resolved_kind || "-"}`,
    `report: ${payload.report_name || "-"}`,
    `truncated: ${payload.truncated ? "yes" : "no"}`,
    "",
    payload.preview_text || "(empty)",
  ]);
  printOutput("보고서 미리보기", payload);
  return payload;
}

async function openReport(taskId = currentTaskId) {
  if (!taskId) {
    printOutput("보고서 열기 오류", { error: "task_id를 먼저 입력하거나 최근 작업에서 선택하세요." });
    return;
  }
  const response = await fetch(`/api/v1/agent/report/${taskId}/raw`, { headers: headers() });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `failed to open report: ${response.status}`);
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  window.open(objectUrl, "_blank", "noopener");
  setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
  printOutput("보고서 원문 열기", { task_id: taskId, raw_url: `/api/v1/agent/report/${taskId}/raw` });
}

async function loadAgentStatus(taskId = currentTaskId) {
  if (!taskId) {
    printOutput("상태 조회 오류", { error: "task_id를 먼저 입력하거나 요청을 제출하세요." });
    return;
  }
  const payload = await requestJson(`/api/v1/agent/status/${taskId}`);
  currentTaskId = payload.task_id || taskId;
  agentTaskIdInput.value = currentTaskId;
  agentResolvedKindInput.value = payload.resolved_kind || "";
  agentStatusInput.value = payload.status || "";
  const result = payload.result || {};
  const stateSummary = payload.state_summary || {};
  setAgentSummary([
    `task_id: ${payload.task_id || "-"}`,
    `resolved_kind: ${payload.resolved_kind || "-"}`,
    `status: ${payload.status || "-"}`,
    `canonical_state: ${stateSummary.canonical_state || "-"}`,
    `canonical_reason: ${stateSummary.canonical_reason_code || "-"}`,
    stateSummary.detail_reason_code ? `detail_reason: ${stateSummary.detail_reason_code}` : "",
    `next_action: ${payload.next_action || "-"}`,
    result.report_path ? `report_path: ${result.report_path}` : "",
    result.actions_executed !== undefined ? `actions_executed: ${result.actions_executed}` : "",
  ].filter(Boolean));
  setPlannerSummary(plannerSummaryLines(payload));
  setPlannerRationale(rationaleLines(payload));
  renderSignalStrip(payload);
  renderActionInspector(planDetail, payload?.planned_actions || [], actionStepMarkup, "아직 action sequence가 없습니다.");
  renderActionInspector(
    executionDetail,
    payload?.action_results || [],
    executionStepMarkup,
    "아직 execution detail이 없습니다."
  );
  if (!result.report_path) {
    setReportPreview("아직 생성된 보고서가 없습니다.");
  }
  printOutput("Agent 상태", payload);
  if (payload.status === "NEEDS_HUMAN_APPROVAL" && isElevatedRole()) {
    await loadApprovals();
  }
  return payload;
}

async function loadAgentEvents(taskId = currentTaskId) {
  if (!taskId) {
    printOutput("이벤트 조회 오류", { error: "task_id를 먼저 입력하거나 요청을 제출하세요." });
    return;
  }
  const payload = await requestJson(`/api/v1/agent/events/${taskId}`);
  const eventPreview = (payload.items || [])
    .slice(-6)
    .map((item) => `${item.created_at || "-"} ${item.event_type || "-"}`);
  if (eventPreview.length) {
    setAgentSummary(eventPreview);
  }
  printOutput("Agent 이벤트", payload);
}

async function submitAgent() {
  const requestedBy = actorIdInput.value.trim() || "qa_user";
  const payload = await requestJson("/api/v1/agent/submit", {
    method: "POST",
    body: JSON.stringify({
      task_kind: agentTaskKindSelect.value,
      title: agentTitleInput.value.trim() || null,
      request_text: agentRequestTextInput.value.trim(),
      requested_by: requestedBy,
      metadata: parseMetadataInput(),
      auto_run: true,
      incident_run_mode: agentRunModeSelect.value,
    }),
  });
  currentTaskId = payload.task_id || "";
  agentTaskIdInput.value = currentTaskId;
  agentResolvedKindInput.value = payload.resolved_kind || "";
  agentStatusInput.value = payload.status || "";
  setAgentSummary([
    `task_id: ${payload.task_id || "-"}`,
    `resolved_kind: ${payload.resolved_kind || "-"}`,
    `status: ${payload.status || "-"}`,
    `entrypoint: ${payload.entrypoint || "-"}`,
  ]);
  printOutput("Agent 제출 결과", payload);
  const statusPayload = await loadAgentStatus(currentTaskId);
  if (((statusPayload || {}).result || {}).report_path) {
    await loadReportPreview(currentTaskId);
  }
}

async function loadApprovals() {
  if (!isElevatedRole()) {
    approvalList.innerHTML = "";
    printOutput("승인 목록", { note: "approver/admin role에서만 승인 큐를 조회합니다." });
    return;
  }
  const params = new URLSearchParams();
  if (approvalStatusFilterSelect.value) {
    params.set("status", approvalStatusFilterSelect.value);
  }
  if (approvalGroupFilterInput.value.trim()) {
    params.set("approver_group", approvalGroupFilterInput.value.trim());
  }
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const payload = await requestJson(`/api/v1/approvals${suffix}`);
  renderApprovals(payload.items || []);
  printOutput("승인 목록", payload);
}

async function loadRecentApprovals() {
  if (!isElevatedRole()) {
    recentApprovalList.innerHTML = "";
    printOutput("최근 승인", { note: "approver/admin role에서만 최근 승인 이력을 봅니다." });
    return;
  }
  const payload = await requestJson("/api/v1/approvals");
  const items = [...(payload.items || [])]
    .sort((left, right) => String(right.resolved_at || right.created_at || "").localeCompare(String(left.resolved_at || left.created_at || "")))
    .slice(0, 8);
  renderRecentApprovals(items);
  printOutput("최근 승인", { items, count: items.length });
}

async function loadApprovalDetail(queueId = currentApprovalQueueId) {
  if (!isElevatedRole()) {
    setApprovalDetail("approver/admin 역할에서만 승인 상세와 이력을 확인할 수 있습니다.");
    printOutput("승인 상세", { note: "approval detail requires approver/admin role" });
    return null;
  }
  if (!queueId) {
    printOutput("승인 상세 오류", { error: "queue_id를 먼저 선택하세요." });
    return null;
  }
  const payload = await requestJson(`/api/v1/approvals/${queueId}`);
  currentApprovalQueueId = queueId;
  approvalDetailIdInput.value = queueId;
  const historyLines = (payload.actions || []).length
    ? payload.actions.map(
        (item) =>
          `${item.created_at || "-"} ${item.action || "-"} by ${item.acted_by || "-"}${item.comment ? ` :: ${item.comment}` : ""}`
      )
    : ["이력이 아직 없습니다."];
  const item = payload.item || {};
  const taskSummary = payload.task_summary || {};
  setApprovalDetail([
    `queue_id: ${payload.queue_id || "-"}`,
    `status: ${item.status || "-"}`,
    `reason: ${item.reason_code || "-"}`,
    `approver_group: ${item.approver_group || "-"}`,
    `requested_by: ${item.requested_by || "-"}`,
    `task_id: ${taskSummary.task_id || item.task_id || "-"}`,
    `task_status: ${taskSummary.status || "-"}`,
    "",
    "history:",
    ...historyLines,
  ]);
  printOutput("승인 상세", payload);
  return payload;
}

async function actApproval(queueId, action) {
  if (!isElevatedRole()) {
    printOutput("승인 처리 오류", { error: "approver/admin role에서만 승인 처리를 할 수 있습니다." });
    return;
  }
  const payload = await requestJson(`/api/v1/approvals/${queueId}/${action}`, {
    method: "POST",
    body: JSON.stringify({
      acted_by: actedByInput.value.trim() || "qa_approver",
      comment: approvalCommentInput.value.trim() || null,
    }),
  });
  printOutput(`승인 ${action} 결과`, payload);
  await loadApprovals();
  await loadRecentApprovals();
  await loadApprovalDetail(queueId);
  if (currentTaskId) {
    await loadAgentStatus(currentTaskId);
  }
}

async function createDraft() {
  const requestedBy = actorIdInput.value.trim() || "qa_user";
  const payload = await requestJson("/api/v1/tool-drafts", {
    method: "POST",
    body: JSON.stringify({
      requested_by: requestedBy,
      request_text: draftRequestTextInput.value.trim(),
      tool_id: draftToolIdInput.value.trim() || null,
      title: draftTitleInput.value.trim() || null,
    }),
  });
  draftIdInput.value = payload.draft_id || "";
  printOutput("Draft 생성 결과", payload);
  await loadTools();
}

async function loadDraft() {
  const draftId = draftIdInput.value.trim();
  if (!draftId) {
    printOutput("Draft 조회 오류", { error: "draft_id를 먼저 입력하세요." });
    return;
  }
  const payload = await requestJson(`/api/v1/tool-drafts/${draftId}`);
  printOutput("Draft 조회 결과", payload);
}

async function applyDraft() {
  if (!isElevatedRole()) {
    printOutput("Draft 적용 오류", { error: "approver/admin role에서만 draft 적용을 할 수 있습니다." });
    return;
  }
  const draftId = draftIdInput.value.trim();
  if (!draftId) {
    printOutput("Draft 적용 오류", { error: "draft_id를 먼저 입력하세요." });
    return;
  }
  const payload = await requestJson(`/api/v1/tool-drafts/${draftId}/apply`, {
    method: "POST",
    body: JSON.stringify({
      acted_by: actedByInput.value.trim() || "qa_approver",
    }),
  });
  printOutput("Draft 적용 결과", payload);
  await loadTools();
}

document.querySelector("#refresh-tools").addEventListener("click", async () => {
  try {
    await loadTools();
  } catch (error) {
    printOutput("도구 목록 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#load-task-example").addEventListener("click", () => {
  fillAgentExample("task");
});

document.querySelector("#load-incident-example").addEventListener("click", () => {
  fillAgentExample("incident");
});

document.querySelector("#load-approval-example").addEventListener("click", () => {
  fillAgentExample("approval");
});

document.querySelector("#submit-agent").addEventListener("click", async () => {
  try {
    await submitAgent();
  } catch (error) {
    printOutput("Agent 제출 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#refresh-status").addEventListener("click", async () => {
  try {
    await loadAgentStatus(agentTaskIdInput.value.trim() || currentTaskId);
  } catch (error) {
    printOutput("상태 조회 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#refresh-events").addEventListener("click", async () => {
  try {
    await loadAgentEvents(agentTaskIdInput.value.trim() || currentTaskId);
  } catch (error) {
    printOutput("이벤트 조회 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#preview-report").addEventListener("click", async () => {
  try {
    await loadReportPreview(agentTaskIdInput.value.trim() || currentTaskId);
  } catch (error) {
    printOutput("보고서 미리보기 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#open-report").addEventListener("click", async () => {
  try {
    await openReport(agentTaskIdInput.value.trim() || currentTaskId);
  } catch (error) {
    printOutput("보고서 열기 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#refresh-approvals").addEventListener("click", async () => {
  try {
    await loadApprovals();
  } catch (error) {
    printOutput("승인 목록 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#refresh-recent").addEventListener("click", async () => {
  try {
    await loadRecentTasks();
  } catch (error) {
    printOutput("최근 작업 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#refresh-job-history").addEventListener("click", async () => {
  try {
    await loadJobHistory();
  } catch (error) {
    printOutput("Job 실행 이력 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#refresh-harness").addEventListener("click", async () => {
  try {
    await loadHarness();
  } catch (error) {
    printOutput("LLM Harness 조회 오류", { error: String(error.message || error) });
  }
});

jobHistoryTemplateSelect.addEventListener("change", async () => {
  try {
    await loadJobHistory();
  } catch (error) {
    printOutput("Job 실행 이력 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#refresh-approval-history").addEventListener("click", async () => {
  try {
    await loadRecentApprovals();
  } catch (error) {
    printOutput("최근 승인 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#load-approval-detail").addEventListener("click", async () => {
  try {
    await loadApprovalDetail(approvalDetailIdInput.value.trim() || currentApprovalQueueId);
  } catch (error) {
    printOutput("승인 상세 오류", { error: String(error.message || error) });
  }
});

jobRunList.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  const taskId = target.dataset.loadJobTask;
  const previewTaskId = target.dataset.previewJobReport;
  if (previewTaskId) {
    currentTaskId = previewTaskId;
    agentTaskIdInput.value = previewTaskId;
    try {
      await loadReportPreview(previewTaskId);
    } catch (error) {
      printOutput("Job 보고서 미리보기 오류", { error: String(error.message || error) });
    }
    return;
  }
  if (!taskId) {
    return;
  }
  currentTaskId = taskId;
  agentTaskIdInput.value = taskId;
  try {
    const payload = await loadAgentStatus(taskId);
    if (((payload || {}).result || {}).report_path) {
      await loadReportPreview(taskId);
    }
  } catch (error) {
    printOutput("Job 상태 보기 오류", { error: String(error.message || error) });
  }
});

recentTaskList.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  const taskId = target.dataset.loadTask;
  const previewTaskId = target.dataset.previewReport;
  const openTaskId = target.dataset.openReport;
  if (previewTaskId) {
    currentTaskId = previewTaskId;
    agentTaskIdInput.value = previewTaskId;
    try {
      await loadReportPreview(previewTaskId);
    } catch (error) {
      printOutput("최근 작업 보고서 미리보기 오류", { error: String(error.message || error) });
    }
    return;
  }
  if (openTaskId) {
    currentTaskId = openTaskId;
    agentTaskIdInput.value = openTaskId;
    try {
      await openReport(openTaskId);
    } catch (error) {
      printOutput("최근 작업 보고서 열기 오류", { error: String(error.message || error) });
    }
    return;
  }
  if (!taskId) {
    return;
  }
  currentTaskId = taskId;
  agentTaskIdInput.value = taskId;
  try {
    const payload = await loadAgentStatus(taskId);
    await loadAgentEvents(taskId);
    if (((payload || {}).result || {}).report_path) {
      await loadReportPreview(taskId);
    }
  } catch (error) {
    printOutput("최근 작업 불러오기 오류", { error: String(error.message || error) });
  }
});

recentApprovalList.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  const queueId = target.dataset.approvalDetail;
  if (!queueId) {
    return;
  }
  currentApprovalQueueId = queueId;
  approvalDetailIdInput.value = queueId;
  try {
    await loadApprovalDetail(queueId);
  } catch (error) {
    printOutput("최근 승인 상세 오류", { error: String(error.message || error) });
  }
});

approvalList.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  const detailId = target.dataset.approvalDetail;
  const approveId = target.dataset.approve;
  const rejectId = target.dataset.reject;
  try {
    if (detailId) {
      currentApprovalQueueId = detailId;
      approvalDetailIdInput.value = detailId;
      await loadApprovalDetail(detailId);
    } else if (approveId) {
      await actApproval(approveId, "approve");
    } else if (rejectId) {
      await actApproval(rejectId, "reject");
    }
  } catch (error) {
    printOutput("승인 처리 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#create-draft").addEventListener("click", async () => {
  try {
    await createDraft();
  } catch (error) {
    printOutput("Draft 생성 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#load-draft").addEventListener("click", async () => {
  try {
    await loadDraft();
  } catch (error) {
    printOutput("Draft 조회 오류", { error: String(error.message || error) });
  }
});

document.querySelector("#apply-draft").addEventListener("click", async () => {
  try {
    await applyDraft();
  } catch (error) {
    printOutput("Draft 적용 오류", { error: String(error.message || error) });
  }
});

actorRoleSelect.addEventListener("change", async () => {
  applyRoleVisibility();
  try {
    await loadCapabilities();
    await loadRecentTasks();
    await loadJobHistory();
    await loadHarness();
  } catch (error) {
    printOutput("Capability 로딩 오류", { error: String(error.message || error) });
  }
});

applyRoleVisibility();
await loadHealth();
try {
  await loadCapabilities();
  fillAgentExample("task");
  await loadTools();
  await loadRecentTasks();
  await loadJobHistory();
  await loadHarness();
  setPlannerSummary("아직 planner 정보가 없습니다.");
  setPlannerRationale("아직 planner rationale이 없습니다.");
  renderSignalStrip({});
  setPlanDetail("아직 action sequence가 없습니다.");
  setExecutionDetail("아직 execution detail이 없습니다.");
  setReportPreview("아직 생성된 보고서가 없습니다.");
  setApprovalDetail("아직 선택된 승인 항목이 없습니다.");
} catch (error) {
  printOutput("초기 로딩 오류", { error: String(error.message || error) });
}
