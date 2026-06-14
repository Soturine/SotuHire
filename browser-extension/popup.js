const API = "http://127.0.0.1:8765";
const result = document.querySelector("#result");
const useAI = document.querySelector("#use-ai");
const localToken = document.querySelector("#local-token");

chrome.storage.local.get(["useAI", "localToken"], (saved) => {
  useAI.checked = Boolean(saved.useAI);
  localToken.value = saved.localToken || "";
});
useAI.addEventListener("change", () => chrome.storage.local.set({ useAI: useAI.checked }));
localToken.addEventListener("change", () => chrome.storage.local.set({ localToken: localToken.value }));

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
