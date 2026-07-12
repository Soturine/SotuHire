const API = "http://127.0.0.1:8765";
const result = document.querySelector("#result");
const localToken = document.querySelector("#local-token");
const deepProjectAnalysis = document.querySelector("#deep-project-analysis");
const aiProvider = document.querySelector("#ai-provider");
const aiModel = document.querySelector("#ai-model");
const aiApiKey = document.querySelector("#ai-api-key");
const rememberKey = document.querySelector("#remember-key");
const externalKeySettings = document.querySelector("#external-key-settings");
const providerKeyLink = document.querySelector("#provider-key-link");
const providerHelp = document.querySelector("#provider-help");
const providerStatus = document.querySelector("#provider-status");
const catalogStatus = document.querySelector("#catalog-status");
const keyState = document.querySelector("#key-state");
let providerConfiguration = {};

initialize().catch((error) => showError(error.message));

async function initialize() {
  const saved = await chrome.storage.local.get([
    "aiProvider",
    "aiModels",
    "localToken",
    "deepProjectAnalysis",
  ]);
  localToken.value = saved.localToken || "";
  deepProjectAnalysis.checked = Boolean(saved.deepProjectAnalysis);
  aiProvider.value = saved.aiProvider || "sotuhire";
  const tab = await currentTab();
  document.querySelector("#page-title").textContent =
    tab?.title || "Capturar e analisar";
  await refreshAiStatus();
  await loadModels(false, saved.aiModels?.[aiProvider.value]);
  await checkCompanion();
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => {
      const active = item === tab;
      item.classList.toggle("active", active);
      item.setAttribute("aria-selected", String(active));
    });
    document.querySelectorAll(".tab-panel").forEach((panel) => {
      const active = panel.id === tab.dataset.tab;
      panel.classList.toggle("active", active);
      panel.hidden = !active;
    });
  });
});

localToken.addEventListener("change", () =>
  chrome.storage.local.set({ localToken: localToken.value }),
);
deepProjectAnalysis.addEventListener("change", () => {
  chrome.storage.local.set({
    deepProjectAnalysis: deepProjectAnalysis.checked,
  });
});
aiProvider.addEventListener("change", async () => {
  await chrome.storage.local.set({ aiProvider: aiProvider.value });
  updateProviderUi();
  await loadModels(false);
});
aiModel.addEventListener("change", async () => {
  const saved = await chrome.storage.local.get(["aiModels"]);
  await chrome.storage.local.set({
    aiModels: { ...(saved.aiModels || {}), [aiProvider.value]: aiModel.value },
  });
  updateProviderSummary();
});
document.querySelector("#toggle-secret").addEventListener("click", () => {
  aiApiKey.type = aiApiKey.type === "password" ? "text" : "password";
});

const currentTab = async () =>
  (await chrome.tabs.query({ active: true, currentWindow: true }))[0];

const extract = async (type = "SOTUHIRE_CAPTURE") => {
  const tab = await currentTab();
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ["content.js"],
  });
  return chrome.tabs.sendMessage(tab.id, {
    type,
    deep: deepProjectAnalysis.checked,
  });
};

const backgroundRequest = async (message) => {
  const response = await chrome.runtime.sendMessage(message);
  if (!response?.ok)
    throw new Error(
      response?.error || "O service worker da extensão não respondeu.",
    );
  return response;
};

const request = async (path, body) => {
  try {
    const response = await fetch(`${API}${path}`, {
      method: body ? "POST" : "GET",
      headers: {
        "Content-Type": "application/json",
        "X-SotuHire-Token": localToken.value,
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    const payload = await response.json();
    if (!response.ok || payload.ok === false)
      throw new Error(payload.message || `HTTP ${response.status}`);
    return payload;
  } catch (error) {
    throw new Error(
      `Local Companion offline. Inicie o SotuHire local e tente novamente. ${error.message}`,
    );
  }
};

async function checkCompanion() {
  try {
    const payload = await request("/health");
    setCompanionState(true, payload.message || "SotuHire conectado");
    return payload;
  } catch (error) {
    setCompanionState(false, "SotuHire offline · modo independente ativo");
    return { ok: false, message: error.message };
  }
}

function setCompanionState(online, label) {
  document.querySelector("#companion-dot").className =
    `status-dot ${online ? "online" : "offline"}`;
  document.querySelector("#companion-status").textContent = label;
}

function showResult(title, message, icon = "✓") {
  result.className = "result-card";
  result.innerHTML = `<span class="result-icon">${icon}</span><div><strong></strong><p></p></div>`;
  result.querySelector("strong").textContent = title;
  result.querySelector("p").textContent = message;
}

function showError(message) {
  result.className = "result-card error";
  result.innerHTML =
    '<span class="result-icon">!</span><div><strong>Não foi possível concluir</strong><p></p></div>';
  result.querySelector("p").textContent =
    `${message}\nVocê ainda pode copiar o texto ou acumular um lote offline.`;
}

const display = (payload) => {
  if (payload.profile_summary || payload.enabled_flows) {
    showResult(
      `SotuHire ${payload.app_version || ""}`.trim(),
      [
        payload.profile_available
          ? "Perfil: resumo seguro disponível"
          : "Perfil: sem resumo seguro",
        `IA: ${payload.ai_provider_status || "local"}`,
        `Fluxos: ${(payload.enabled_flows || []).join(", ")}`,
        ...(payload.warnings || []),
      ]
        .filter(Boolean)
        .join("\n"),
      "⌁",
    );
    return;
  }
  if (payload.report) {
    const report = payload.report;
    const trace = report.provider_used
      ? `\n${report.provider_used} · ${report.model_used || report.provider_used}${report.fallback_used ? " · fallback local" : ""}`
      : "";
    showResult(
      `${report.overall_score}/100 · Grade ${report.grade}`,
      `${report.summary || payload.message || "Relatório concluído."}${trace}`,
      "✦",
    );
    return;
  }
  const scores =
    payload.match_score == null
      ? ""
      : `\nMatch: ${payload.match_score} · ATS: ${payload.ats_score}`;
  showResult("Ação concluída", `${payload.message || "Concluído."}${scores}`);
};

async function refreshAiStatus() {
  const status = await backgroundRequest({ type: "SOTUHIRE_AI_STATUS" });
  providerConfiguration = status.providers || {};
  aiProvider.value = status.provider || aiProvider.value;
  updateProviderUi();
}

function updateProviderUi() {
  const provider = aiProvider.value;
  const external = ["gemini", "openai"].includes(provider);
  externalKeySettings.hidden = !external;
  if (provider === "gemini") {
    providerKeyLink.href = "https://aistudio.google.com/app/apikey";
    providerHelp.textContent =
      "Gemini roda diretamente no service worker da extensão.";
  } else if (provider === "openai") {
    providerKeyLink.href = "https://platform.openai.com/api-keys";
    providerHelp.textContent =
      "OpenAI roda diretamente no service worker da extensão.";
  } else if (provider === "sotuhire") {
    providerHelp.textContent =
      "A chave permanece no backend local do SotuHire.";
  } else {
    providerHelp.textContent =
      "Análise determinística no navegador, sem provider externo.";
  }
  if (external) {
    const config = providerConfiguration[provider] || {};
    keyState.textContent = config.configured
      ? config.persistent
        ? "Chave salva neste perfil"
        : "Chave ativa nesta sessão"
      : "Chave não configurada";
    rememberKey.checked = Boolean(config.persistent);
  } else {
    keyState.textContent =
      provider === "sotuhire" ? "Backend local" : "Sem chave";
  }
  updateProviderSummary();
}

function updateProviderSummary() {
  const label =
    aiProvider.options[aiProvider.selectedIndex]?.text || aiProvider.value;
  providerStatus.textContent = `${label} · ${aiModel.value || "carregando modelo"}`;
}

async function loadModels(force, preferred = "") {
  catalogStatus.textContent = force
    ? "Consultando catálogo oficial…"
    : "Carregando modelos…";
  const payload = await backgroundRequest({
    type: "SOTUHIRE_AI_LIST_MODELS",
    provider: aiProvider.value,
    force,
  });
  const saved = await chrome.storage.local.get(["aiModels"]);
  const selected =
    preferred ||
    saved.aiModels?.[aiProvider.value] ||
    payload.models?.[0] ||
    "";
  const models = [
    ...new Set([selected, ...(payload.models || [])].filter(Boolean)),
  ];
  aiModel.replaceChildren(...models.map((model) => new Option(model, model)));
  aiModel.value = selected || models[0] || "";
  await chrome.storage.local.set({
    aiModels: { ...(saved.aiModels || {}), [aiProvider.value]: aiModel.value },
  });
  catalogStatus.textContent =
    payload.warning ||
    `${models.length} modelo(s) · fonte ${payload.source}${payload.refreshedAt ? ` · ${new Date(payload.refreshedAt).toLocaleString("pt-BR")}` : ""}`;
  updateProviderSummary();
  return payload;
}

const applicationIdentity = (item) => {
  let url = item.url;
  try {
    const parsed = new URL(item.url);
    for (const key of [...parsed.searchParams.keys()]) {
      if (
        key.startsWith("utm_") ||
        ["ref", "tracking", "gclid", "fbclid"].includes(key)
      ) {
        parsed.searchParams.delete(key);
      }
    }
    parsed.hash = "";
    url = parsed.toString().replace(/\/$/, "");
  } catch (_error) {
    url = item.url;
  }
  return `${url}|${item.job_title.trim().toLowerCase()}|${item.company.trim().toLowerCase()}`;
};

const queuePendingAction = async (path, body, label) => {
  const saved = await chrome.storage.local.get(["pendingCompanionActions"]);
  const pending = saved.pendingCompanionActions || [];
  const identity = `${path}|${body.capture_id || body.url || body.capture?.url || ""}`;
  const filtered = pending.filter((item) => item.identity !== identity);
  filtered.push({
    identity,
    path,
    body,
    label,
    queuedAt: new Date().toISOString(),
  });
  await chrome.storage.local.set({ pendingCompanionActions: filtered });
  return filtered.length;
};

const sendOrQueue = async (path, body, label) => {
  try {
    return await request(path, body);
  } catch (error) {
    const count = await queuePendingAction(path, body, label);
    throw new Error(
      `${error.message} ${label} mantida localmente (${count} pendência(s)).`,
    );
  }
};

const retryPending = async () => {
  const saved = await chrome.storage.local.get(["pendingCompanionActions"]);
  const pending = saved.pendingCompanionActions || [];
  if (!pending.length) return { message: "Não há pendências offline." };
  const remaining = [];
  let sent = 0;
  for (const item of pending) {
    try {
      await request(item.path, item.body);
      sent += 1;
    } catch (_error) {
      remaining.push(item);
    }
  }
  await chrome.storage.local.set({ pendingCompanionActions: remaining });
  return {
    message: `${sent} pendência(s) enviada(s); ${remaining.length} ainda aguardam o Companion.`,
  };
};

async function analyzeCurrentProject() {
  const { project } = await extract("SOTUHIRE_PROJECT");
  const payload = await backgroundRequest({
    type: "SOTUHIRE_AI_ANALYZE",
    project,
    options: {
      provider: aiProvider.value,
      model: aiModel.value,
      deep: deepProjectAnalysis.checked,
    },
  });
  await chrome.storage.local.set({
    lastProjectAnalysis: {
      project: payload.project,
      report: payload.report,
      savedAt: new Date().toISOString(),
    },
  });
  display(payload);
}

const act = async (action) => {
  showResult("Processando…", "Coletando somente os dados necessários.", "…");
  try {
    if (action === "health") return display(await checkCompanion());
    if (action === "context-summary")
      return display(await request("/capture/context-summary"));
    if (action === "refresh-models") {
      const catalog = await loadModels(true);
      return display({
        message:
          catalog.warning ||
          `${catalog.models?.length || 0} modelos atualizados pela fonte ${catalog.source}.`,
      });
    }
    if (action === "save-key") {
      const payload = await backgroundRequest({
        type: "SOTUHIRE_AI_SAVE_KEY",
        provider: aiProvider.value,
        apiKey: aiApiKey.value,
        remember: rememberKey.checked,
      });
      aiApiKey.value = "";
      await refreshAiStatus();
      await loadModels(false);
      return display({
        message: `Chave validada. ${payload.models?.length || 0} modelos disponíveis.`,
      });
    }
    if (action === "remove-key") {
      await backgroundRequest({
        type: "SOTUHIRE_AI_REMOVE_KEY",
        provider: aiProvider.value,
      });
      aiApiKey.value = "";
      await refreshAiStatus();
      return display({
        message: "Chave removida da sessão e do perfil do navegador.",
      });
    }
    if (action === "retry-pending") return display(await retryPending());
    if (action === "applications") {
      const payload = await extract("SOTUHIRE_APPLICATIONS");
      return display(
        await sendOrQueue(
          "/capture/applications",
          payload,
          "Lote de candidaturas",
        ),
      );
    }
    if (action === "collect-page") {
      const payload = await extract("SOTUHIRE_APPLICATIONS");
      const saved = await chrome.storage.local.get(["applicationBatch"]);
      const current = saved.applicationBatch || [];
      const identities = new Set(current.map(applicationIdentity));
      payload.applications.forEach((item) => {
        const identity = applicationIdentity(item);
        if (!identities.has(identity)) {
          identities.add(identity);
          current.push(item);
        }
      });
      await chrome.storage.local.set({ applicationBatch: current });
      return display({
        message: `${current.length} candidaturas acumuladas no lote.`,
      });
    }
    if (action === "send-batch") {
      const saved = await chrome.storage.local.get(["applicationBatch"]);
      const applications = saved.applicationBatch || [];
      if (!applications.length)
        return display({ message: "O lote está vazio." });
      const response = await request("/capture/applications", { applications });
      await chrome.storage.local.remove(["applicationBatch"]);
      return display(response);
    }
    if (action === "project-standalone") return analyzeCurrentProject();
    if (action.startsWith("project-")) {
      const { project } = await extract("SOTUHIRE_PROJECT");
      const savedAnalysis = await chrome.storage.local.get([
        "lastProjectAnalysis",
      ]);
      const paths = {
        "project-connected": "/capture/repo-analysis",
        "project-evidence": "/capture/project",
        "project-compare": "/capture/repo-analysis",
        "project-memory": "/capture/project",
        "project-profile": "/capture/project",
      };
      project.provider_used = "local";
      project.analysis_result = {
        ...(project.analysis_result || {}),
        use_ai: aiProvider.value === "sotuhire",
        extension_ai_report: savedAnalysis.lastProjectAnalysis?.report || null,
      };
      return display(
        await sendOrQueue(paths[action], project, "Projeto público"),
      );
    }
    const { capture } = await extract();
    if (action === "copy") {
      await navigator.clipboard.writeText(capture.visible_text);
      return display({ message: "Texto visível copiado." });
    }
    if (action === "capture-public-exam") {
      return display(
        await sendOrQueue(
          "/capture/public-exam",
          {
            ...capture,
            kind: "public_exam",
            job_title: "",
            company: "",
          },
          "Captura de edital",
        ),
      );
    }
    const paths = {
      capture: "/capture/job",
      analyze: "/capture/analyze",
      tracker: "/capture/tracker",
    };
    const body =
      action === "capture"
        ? capture
        : { capture, use_ai: aiProvider.value === "sotuhire" };
    display(await sendOrQueue(paths[action], body, "Captura de vaga"));
  } catch (error) {
    showError(error.message);
  }
};

document.querySelectorAll("button[data-action]").forEach((button) => {
  button.addEventListener("click", () => act(button.dataset.action));
});
