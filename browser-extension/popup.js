const API = "http://127.0.0.1:8765";
const result = document.querySelector("#result");
const useAI = document.querySelector("#use-ai");
const localToken = document.querySelector("#local-token");
const standaloneGeminiKey = document.querySelector("#standalone-gemini-key");

chrome.storage.local.get(["useAI", "localToken", "standaloneGeminiKey"], (saved) => {
  useAI.checked = Boolean(saved.useAI);
  localToken.value = saved.localToken || "";
  standaloneGeminiKey.value = saved.standaloneGeminiKey || "";
});
useAI.addEventListener("change", () => chrome.storage.local.set({ useAI: useAI.checked }));
localToken.addEventListener("change", () => chrome.storage.local.set({ localToken: localToken.value }));
standaloneGeminiKey.addEventListener("change", () => chrome.storage.local.set({
  standaloneGeminiKey: standaloneGeminiKey.value
}));

const currentTab = async () => (await chrome.tabs.query({ active: true, currentWindow: true }))[0];

const extract = async (type = "SOTUHIRE_CAPTURE") => {
  const tab = await currentTab();
  await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
  return chrome.tabs.sendMessage(tab.id, { type });
};

const request = async (path, body) => {
  const response = await fetch(`${API}${path}`, {
    method: body ? "POST" : "GET",
    headers: {
      "Content-Type": "application/json",
      "X-SotuHire-Token": localToken.value
    },
    body: body ? JSON.stringify(body) : undefined
  });
  return response.json();
};

const display = (payload) => {
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

const analyzeWithStandaloneGemini = async (project, localReport) => {
  if (!standaloneGeminiKey.value) return localReport;
  const granted = await chrome.permissions.request({
    origins: ["https://generativelanguage.googleapis.com/*"]
  });
  if (!granted) throw new Error("Permissão do Gemini standalone não concedida.");
  const prompt = [
    "Avalie este projeto público sem inventar fatos. Responda em português com resumo,",
    "pontos fortes, pontos fracos e prioridades.",
    JSON.stringify({ project, local_report: localReport })
  ].join("\n");
  const response = await fetch(
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-goog-api-key": standaloneGeminiKey.value
      },
      body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
    }
  );
  if (!response.ok) throw new Error(`Gemini standalone falhou: HTTP ${response.status}`);
  const payload = await response.json();
  localReport.gemini_summary = payload.candidates?.[0]?.content?.parts?.[0]?.text || "";
  return localReport;
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

const act = async (action) => {
  result.textContent = "Processando localmente...";
  try {
    if (action === "health") return display(await request("/health"));
    if (action === "applications") {
      const payload = await extract("SOTUHIRE_APPLICATIONS");
      return display(await request("/capture/applications", payload));
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
        const report = await analyzeWithStandaloneGemini(
          project,
          SotuHireProjectAnalyzer.analyze(project)
        );
        result.textContent = `${report.summary}\nStack: ${(report.stack || []).join(", ")}\n${report.gemini_summary || ""}`;
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
      return display(await request(paths[action], project));
    }
    const { capture } = await extract();
    if (action === "copy") {
      await navigator.clipboard.writeText(capture.visible_text);
      return display({ message: "Texto visível copiado." });
    }
    const paths = {
      capture: "/capture/job",
      analyze: "/capture/analyze",
      tracker: "/capture/tracker"
    };
    const body = action === "capture" ? capture : { capture, use_ai: useAI.checked };
    display(await request(paths[action], body));
  } catch (error) {
    result.textContent = `Falha: ${error.message}`;
  }
};

document.querySelectorAll("button[data-action]").forEach((button) => {
  button.addEventListener("click", () => act(button.dataset.action));
});
