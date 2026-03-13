const actorIdInput = document.querySelector("#actor-id");
const actorRoleSelect = document.querySelector("#actor-role");
const actedByInput = document.querySelector("#acted-by");
const filterFamilyInput = document.querySelector("#filter-family");
const filterSystemInput = document.querySelector("#filter-system");
const draftRequestTextInput = document.querySelector("#draft-request-text");
const draftToolIdInput = document.querySelector("#draft-tool-id");
const draftTitleInput = document.querySelector("#draft-title");
const draftIdInput = document.querySelector("#draft-id");
const output = document.querySelector("#output");
const toolList = document.querySelector("#tool-list");
const healthBadge = document.querySelector("#health-badge");

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
  await loadTools();
} catch (error) {
  printOutput("초기 로딩 오류", { error: String(error.message || error) });
}
