const API = "http://127.0.0.1:8765";
const result = document.querySelector("#result");
const useAI = document.querySelector("#use-ai");
const localToken = document.querySelector("#local-token");
const deepProjectAnalysis = document.querySelector("#deep-project-analysis");

chrome.storage.local.get(["useAI", "localToken", "deepProjectAnalysis"], (saved) => {
  useAI.checked = Boolean(saved.useAI);
  localToken.value = saved.localToken || "";
  deepProjectAnalysis.checked = Boolean(saved.deepProjectAnalysis);
});
useAI.addEventListener("change", () => chrome.storage.local.set({ useAI: useAI.checked }));
localToken.addEventListener("change", () => chrome.storage.local.set({ localToken: localToken.value }));
deepProjectAnalysis.addEventListener("change", () => chrome.storage.local.set({
  deepProjectAnalysis: deepProjectAnalysis.checked
}));

const currentTab = async () => (await chrome.tabs.query({ active: true, currentWindow: true }))[0];

const extract = async (type = "SOTUHIRE_CAPTURE") => {
  const tab = await currentTab();
  await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
  return chrome.tabs.sendMessage(tab.id, { type, deep: deepProjectAnalysis.checked });
};

const request = async (path, body) => {
  try {
    const response = await fetch(`${API}${path}`, {
      method: body ? "POST" : "GET",
      headers: {
        "Content-Type": "application/json",
        "X-SotuHire-Token": localToken.value
      },
      body: body ? JSON.stringify(body) : undefined
    });
    const payload = await response.json();
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.message || `HTTP ${response.status}`);
    }
    return payload;
  } catch (error) {
    throw new Error(
      `Local Companion offline ou indisponível. Inicie o SotuHire local e tente novamente. ${error.message}`
    );
  }
};

const display = (payload) => {
  if (payload.profile_summary || payload.enabled_flows) {
    result.textContent = [
      `SotuHire ${payload.app_version || ""}`.trim(),
      payload.profile_available ? "Perfil: resumo seguro disponível" : "Perfil: sem resumo seguro",
      `IA: ${payload.ai_provider_status || "local"}`,
      `Fluxos: ${(payload.enabled_flows || []).join(", ")}`,
      ...(payload.warnings || [])
    ].filter(Boolean).join("\n");
    return;
  }
  if (payload.report) {
    const report = payload.report;
    result.textContent = `${payload.message || "Relatório concluído."}\nNota: ${report.overall_score}/100 · Grade ${report.grade}\n${report.summary}`;
    return;
  }
  const scores = payload.match_score == null
    ? ""
    : `\nMatch: ${payload.match_score} · ATS: ${payload.ats_score}`;
  result.textContent = `${payload.message || "Concluído."}${scores}`;
};

const applicationIdentity = (item) => {
  let url = item.url;
  try {
    const parsed = new URL(item.url);
    parsed.search = "";
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
  filtered.push({ identity, path, body, label, queuedAt: new Date().toISOString() });
  await chrome.storage.local.set({ pendingCompanionActions: filtered });
  return filtered.length;
};

const sendOrQueue = async (path, body, label) => {
  try {
    return await request(path, body);
  } catch (error) {
    const count = await queuePendingAction(path, body, label);
    throw new Error(`${error.message} ${label} mantida localmente (${count} pendência(s)).`);
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
    message: `${sent} pendência(s) enviada(s); ${remaining.length} ainda aguardam o Companion.`
  };
};

const act = async (action) => {
  result.textContent = "Processando localmente...";
  try {
    if (action === "health") return display(await request("/health"));
    if (action === "context-summary") return display(await request("/capture/context-summary"));
    if (action === "retry-pending") return display(await retryPending());
    if (action === "applications") {
      const payload = await extract("SOTUHIRE_APPLICATIONS");
      return display(await sendOrQueue("/capture/applications", payload, "Lote de candidaturas"));
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
      return display({ message: `${current.length} candidaturas acumuladas no lote.` });
    }
    if (action === "send-batch") {
      const saved = await chrome.storage.local.get(["applicationBatch"]);
      const applications = saved.applicationBatch || [];
      if (!applications.length) return display({ message: "O lote está vazio." });
      const response = await request("/capture/applications", { applications });
      await chrome.storage.local.remove(["applicationBatch"]);
      return display(response);
    }
    if (action.startsWith("project-")) {
      const { project } = await extract("SOTUHIRE_PROJECT");
      if (action === "project-standalone") {
        const report = SotuHireProjectAnalyzer.analyze(project);
        result.textContent = `${report.summary}\nStack: ${(report.stack || []).join(", ")}`;
        return;
      }
      const paths = {
        "project-connected": "/capture/repo-analysis",
        "project-evidence": "/capture/project",
        "project-compare": "/capture/repo-analysis",
        "project-memory": "/capture/project",
        "project-profile": "/capture/project"
      };
      project.provider_used = useAI.checked ? "gemini" : "local";
      return display(await sendOrQueue(paths[action], project, "Projeto público"));
    }
    const { capture } = await extract();
    if (action === "copy") {
      await navigator.clipboard.writeText(capture.visible_text);
      return display({ message: "Texto visível copiado." });
    }
    if (action === "capture-public-exam") {
      return display(await sendOrQueue("/capture/public-exam", {
        ...capture,
        kind: "public_exam",
        job_title: "",
        company: ""
      }, "Captura de edital"));
    }
    const paths = {
      capture: "/capture/job",
      analyze: "/capture/analyze",
      tracker: "/capture/tracker"
    };
    const body = action === "capture" ? capture : { capture, use_ai: useAI.checked };
    display(await sendOrQueue(paths[action], body, "Captura de vaga"));
  } catch (error) {
    result.textContent = `Falha: ${error.message}\nVocê ainda pode copiar o texto ou acumular um lote offline.`;
  }
};

document.querySelectorAll("button[data-action]").forEach((button) => {
  button.addEventListener("click", () => act(button.dataset.action));
});
