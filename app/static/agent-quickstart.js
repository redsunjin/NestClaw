const actorIdInput = document.querySelector("#quick-actor-id");
const actorRoleSelect = document.querySelector("#quick-actor-role");
const actedByInput = document.querySelector("#quick-acted-by");
const requestInput = document.querySelector("#quick-request");
const healthBadge = document.querySelector("#quick-health");
const statusBox = document.querySelector("#quick-status");
const plannerBox = document.querySelector("#quick-planner");
const approvalBox = document.querySelector("#quick-approval");
const reportBox = document.querySelector("#quick-report");
const recentBox = document.querySelector("#quick-recent");
const output = document.querySelector("#quick-output");

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

function setStatus(lines) {
  statusBox.textContent = Array.isArray(lines) ? lines.join("\n") : String(lines || "");
}

function setPlanner(lines) {
  plannerBox.textContent = Array.isArray(lines) ? lines.join("\n") : String(lines || "");
}

function setApproval(lines) {
  approvalBox.textContent = Array.isArray(lines) ? lines.join("\n") : String(lines || "");
}

function setReport(lines) {
  reportBox.textContent = Array.isArray(lines) ? lines.join("\n") : String(lines || "");
}

function fillExample(kind) {
  if (kind === "incident") {
    requestInput.value = "billing-api 장애 대응용 티켓을 만들고 온콜이 볼 수 있게 정리해줘";
    return;
  }
  if (kind === "approval") {
    requestInput.value = "회의 내용을 정리하고 외부 전송 승인까지 올려줘";
    return;
  }
  requestInput.value = "주간 운영회의 메모를 요약하고 액션 아이템을 정리해줘";
}

function toolFlow(items) {
  const values = (items || []).filter(Boolean);
  return values.length ? values.join(" -> ") : "-";
}

function plannerSummaryFromPayload(payload) {
  const provenance = payload?.planning_provenance || {};
  const providerSelection = provenance.provider_selection || {};
  const plannedTools = (payload?.planned_actions || []).map((item) => item.tool_id).filter(Boolean);
  const executedTools = (payload?.action_results || []).map((item) => item.tool_id).filter(Boolean);
  const lines = [
    `source: ${provenance.source || "-"}`,
    `provider: ${providerSelection.provider_id || "-"}`,
    `degraded: ${provenance.degraded_mode ? "yes" : "no"}`,
    provenance.confidence !== undefined && provenance.confidence !== null ? `confidence: ${provenance.confidence}` : "",
    provenance.fallback_reason ? `fallback_reason: ${provenance.fallback_reason}` : "",
    `planned_tools: ${toolFlow(plannedTools)}`,
    executedTools.length ? `executed_tools: ${toolFlow(executedTools)}` : "",
  ].filter(Boolean);
  return lines.length ? lines : ["아직 planner 정보가 없습니다."];
}

function plannerSummaryFromRecent(item) {
  return [
    `planner: ${item.planning_source || "-"}`,
    item.planning_provider_id ? `provider: ${item.planning_provider_id}` : "",
    item.planning_degraded_mode ? "degraded: yes" : "degraded: no",
    item.planning_fallback_reason ? `fallback: ${item.planning_fallback_reason}` : "",
    `planned_tools: ${toolFlow(item.planned_tool_ids || [])}`,
  ].filter(Boolean);
}

async function loadHealth() {
  try {
    const payload = await requestJson("/health", { headers: { "Content-Type": "application/json" } });
    healthBadge.textContent = payload.status === "ok" ? "서버 정상" : "확인 필요";
    healthBadge.className = `badge ${payload.status === "ok" ? "ok" : "pending"}`;
  } catch (_error) {
    healthBadge.textContent = "서버 오류";
    healthBadge.className = "badge pending";
  }
}

async function loadRecent() {
  const payload = await requestJson("/api/v1/agent/recent?limit=5");
  const items = payload.items || [];
  if (!items.length) {
      recentBox.innerHTML = '<article class="recent-card"><h3>최근 요청 없음</h3><p class="recent-meta">아직 최근 요청이 없습니다.</p></article>';
    return;
  }
  recentBox.innerHTML = items
    .map(
      (item) => `
        <article class="recent-card">
          <h3>${item.title || item.task_id}</h3>
          <p class="recent-meta">task_id: ${item.task_id}</p>
          <p class="recent-meta">kind/status: ${item.resolved_kind} / ${item.status}</p>
          <p class="recent-meta">${plannerSummaryFromRecent(item).join(" | ")}</p>
          <div class="recent-actions">
            <button class="subtle" type="button" data-load-task="${item.task_id}">불러오기</button>
          </div>
        </article>
      `
    )
    .join("");
}

async function loadReport(taskId = currentTaskId) {
  if (!taskId) {
    setReport("보고서가 생성되면 여기에 미리보기가 표시됩니다.");
    return null;
  }
  const payload = await requestJson(`/api/v1/agent/report/${taskId}?max_chars=1500`);
  setReport(payload.preview_text || "(empty)");
  return payload;
}

async function openReport(taskId = currentTaskId) {
  if (!taskId) {
    printOutput("보고서 열기 오류", { error: "task_id가 없습니다." });
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
}

async function loadApprovalDetail(queueId = currentApprovalQueueId) {
  if (!queueId) {
    setApproval("승인 대기 항목이 없습니다.");
    return null;
  }
  const payload = await requestJson(`/api/v1/approvals/${queueId}`);
  currentApprovalQueueId = queueId;
  const item = payload.item || {};
  const actions = payload.actions || [];
  setApproval([
    `queue_id: ${payload.queue_id || "-"}`,
    `status: ${item.status || "-"}`,
    `reason: ${item.reason_code || "-"}`,
    actions.length ? "" : "history: 아직 이력이 없습니다.",
    ...actions.map(
      (entry) =>
        `history: ${entry.created_at || "-"} ${entry.action || "-"} by ${entry.acted_by || "-"}${entry.comment ? ` :: ${entry.comment}` : ""}`
    ),
  ].filter(Boolean));
  return payload;
}

async function loadTask(taskId = currentTaskId) {
  if (!taskId) {
    setStatus("아직 실행된 작업이 없습니다.");
    setApproval("승인 대기 항목이 없습니다.");
    setReport("보고서가 생성되면 여기에 미리보기가 표시됩니다.");
    return null;
  }
  const payload = await requestJson(`/api/v1/agent/status/${taskId}`);
  currentTaskId = payload.task_id || taskId;
  currentApprovalQueueId = payload.approval_queue_id || "";
  setStatus([
    `task_id: ${payload.task_id || "-"}`,
    `kind: ${payload.resolved_kind || "-"}`,
    `status: ${payload.status || "-"}`,
    `next_action: ${payload.next_action || "-"}`,
  ]);
  setPlanner(plannerSummaryFromPayload(payload));
  if (((payload.result || {}).report_path)) {
    await loadReport(currentTaskId);
  } else {
    setReport("보고서가 생성되면 여기에 미리보기가 표시됩니다.");
  }
  if (payload.approval_queue_id) {
    if (["approver", "admin"].includes(actorRoleSelect.value)) {
      await loadApprovalDetail(payload.approval_queue_id);
    } else {
      setApproval([
        `queue_id: ${payload.approval_queue_id}`,
        "승인 필요: approver/admin으로 바꾸고 새로고침하세요.",
      ]);
    }
  } else {
    setApproval("승인 대기 항목이 없습니다.");
  }
  printOutput("현재 실행 상태", payload);
  return payload;
}

async function refreshCurrent() {
  await loadTask(currentTaskId);
  await loadRecent();
}

async function submitQuickRequest() {
  const requestedBy = actorIdInput.value.trim() || "qa_user";
  const requestText = requestInput.value.trim();
  const payload = await requestJson("/api/v1/agent/submit", {
    method: "POST",
    body: JSON.stringify({
      task_kind: "auto",
      request_text: requestText,
      requested_by: requestedBy,
      title: null,
      metadata: {},
      auto_run: true,
      incident_run_mode: "dry-run",
    }),
  });
  currentTaskId = payload.task_id || "";
  printOutput("요청 제출 결과", payload);
  await refreshCurrent();
}

async function actApproval(action) {
  if (!currentApprovalQueueId) {
    printOutput("승인 처리 오류", { error: "approval queue가 없습니다." });
    return;
  }
  const payload = await requestJson(`/api/v1/approvals/${currentApprovalQueueId}/${action}`, {
    method: "POST",
    body: JSON.stringify({
      acted_by: actedByInput.value.trim() || "qa_approver",
      comment: `${action} from quickstart`,
    }),
  });
  printOutput(`승인 ${action} 결과`, payload);
  await refreshCurrent();
}

document.querySelector("#quick-example-task").addEventListener("click", () => fillExample("task"));
document.querySelector("#quick-example-incident").addEventListener("click", () => fillExample("incident"));
document.querySelector("#quick-example-approval").addEventListener("click", () => fillExample("approval"));
document.querySelector("#quick-submit").addEventListener("click", async () => {
  try {
    await submitQuickRequest();
  } catch (error) {
    printOutput("요청 제출 오류", { error: String(error.message || error) });
  }
});
document.querySelector("#quick-refresh").addEventListener("click", async () => {
  try {
    await refreshCurrent();
  } catch (error) {
    printOutput("새로고침 오류", { error: String(error.message || error) });
  }
});
document.querySelector("#quick-open-report").addEventListener("click", async () => {
  try {
    await openReport();
  } catch (error) {
    printOutput("보고서 열기 오류", { error: String(error.message || error) });
  }
});
document.querySelector("#quick-approve").addEventListener("click", async () => {
  try {
    await actApproval("approve");
  } catch (error) {
    printOutput("승인 오류", { error: String(error.message || error) });
  }
});
document.querySelector("#quick-reject").addEventListener("click", async () => {
  try {
    await actApproval("reject");
  } catch (error) {
    printOutput("반려 오류", { error: String(error.message || error) });
  }
});

recentBox.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) {
    return;
  }
  const taskId = target.dataset.loadTask;
  if (!taskId) {
    return;
  }
  currentTaskId = taskId;
  try {
    await refreshCurrent();
  } catch (error) {
    printOutput("최근 요청 로드 오류", { error: String(error.message || error) });
  }
});

await loadHealth();
fillExample("task");
setStatus("아직 실행된 작업이 없습니다.");
setPlanner("아직 planner 정보가 없습니다.");
setApproval("승인 대기 항목이 없습니다.");
setReport("보고서가 생성되면 여기에 미리보기가 표시됩니다.");
try {
  await loadRecent();
} catch (error) {
  printOutput("초기 로딩 오류", { error: String(error.message || error) });
}
