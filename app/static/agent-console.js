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
const recentTaskList = document.querySelector("#recent-task-list");
const recentApprovalList = document.querySelector("#recent-approval-list");
const approvalStatusFilterSelect = document.querySelector("#approval-status-filter");
const approvalGroupFilterInput = document.querySelector("#approval-group-filter");
const approvalCommentInput = document.querySelector("#approval-comment");
const filterFamilyInput = document.querySelector("#filter-family");
const filterSystemInput = document.querySelector("#filter-system");
const draftRequestTextInput = document.querySelector("#draft-request-text");
const draftToolIdInput = document.querySelector("#draft-tool-id");
const draftTitleInput = document.querySelector("#draft-title");
const draftIdInput = document.querySelector("#draft-id");
const output = document.querySelector("#output");
const toolList = document.querySelector("#tool-list");
const approvalList = document.querySelector("#approval-list");
const healthBadge = document.querySelector("#health-badge");
let currentTaskId = "";

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

function setAgentSummary(lines) {
  agentSummary.textContent = Array.isArray(lines) ? lines.join("\n") : String(lines || "");
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
            <button class="button subtle" type="button" data-approve="${item.queue_id}">Approve</button>
            <button class="button danger" type="button" data-reject="${item.queue_id}">Reject</button>
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
          <p class="tool-meta">requested_by: ${item.requested_by}</p>
          <p class="tool-meta">updated_at: ${item.updated_at || "-"}</p>
          <div class="approval-actions">
            <button class="button subtle" type="button" data-load-task="${item.task_id}">불러오기</button>
          </div>
        </article>
      `
    )
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
  setAgentSummary([
    `task_id: ${payload.task_id || "-"}`,
    `resolved_kind: ${payload.resolved_kind || "-"}`,
    `status: ${payload.status || "-"}`,
    `next_action: ${payload.next_action || "-"}`,
    result.report_path ? `report_path: ${result.report_path}` : "",
    result.actions_executed !== undefined ? `actions_executed: ${result.actions_executed}` : "",
  ].filter(Boolean));
  printOutput("Agent 상태", payload);
  if (payload.status === "NEEDS_HUMAN_APPROVAL") {
    await loadApprovals();
  }
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
  await loadAgentStatus(currentTaskId);
}

async function loadApprovals() {
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
  const payload = await requestJson("/api/v1/approvals");
  const items = [...(payload.items || [])]
    .sort((left, right) => String(right.resolved_at || right.created_at || "").localeCompare(String(left.resolved_at || left.created_at || "")))
    .slice(0, 8);
  renderRecentApprovals(items);
  printOutput("최근 승인", { items, count: items.length });
}

async function actApproval(queueId, action) {
  const payload = await requestJson(`/api/v1/approvals/${queueId}/${action}`, {
    method: "POST",
    body: JSON.stringify({
      acted_by: actedByInput.value.trim() || "qa_approver",
      comment: approvalCommentInput.value.trim() || null,
    }),
  });
  printOutput(`승인 ${action} 결과`, payload);
  await loadApprovals();
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

document.querySelector("#refresh-approval-history").addEventListener("click", async () => {
  try {
    await loadRecentApprovals();
  } catch (error) {
    printOutput("최근 승인 오류", { error: String(error.message || error) });
  }
});

recentTaskList.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  const taskId = target.dataset.loadTask;
  if (!taskId) {
    return;
  }
  currentTaskId = taskId;
  agentTaskIdInput.value = taskId;
  try {
    await loadAgentStatus(taskId);
    await loadAgentEvents(taskId);
  } catch (error) {
    printOutput("최근 작업 불러오기 오류", { error: String(error.message || error) });
  }
});

approvalList.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  const approveId = target.dataset.approve;
  const rejectId = target.dataset.reject;
  try {
    if (approveId) {
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

await loadHealth();
try {
  fillAgentExample("task");
  await loadTools();
  await loadRecentTasks();
} catch (error) {
  printOutput("초기 로딩 오류", { error: String(error.message || error) });
}
