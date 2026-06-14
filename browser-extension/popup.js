const API = "http://127.0.0.1:8765";
const result = document.querySelector("#result");
const useAI = document.querySelector("#use-ai");

chrome.storage.local.get(["useAI"], (saved) => {
  useAI.checked = Boolean(saved.useAI);
});
useAI.addEventListener("change", () => chrome.storage.local.set({ useAI: useAI.checked }));

const currentTab = async () => (await chrome.tabs.query({ active: true, currentWindow: true }))[0];

const extract = async (type = "SOTUHIRE_CAPTURE") => {
  const tab = await currentTab();
  await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
  return chrome.tabs.sendMessage(tab.id, { type });
};

const request = async (path, body) => {
  const response = await fetch(`${API}${path}`, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
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

const act = async (action) => {
  result.textContent = "Processando localmente...";
  try {
    if (action === "health") return display(await request("/health"));
    if (action === "applications") {
      const payload = await extract("SOTUHIRE_APPLICATIONS");
      return display(await request("/capture/applications", payload));
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
