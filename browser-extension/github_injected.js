(() => {
  const API = "http://127.0.0.1:8765";
  const ROOT_ID = "sotuhire-github-companion";
  let lastPath = "";
  let currentProject = null;
  let currentReport = null;

  const text = (element) => (element?.innerText || "").replace(/\s+/g, " ").trim();
  const unique = (values) => [...new Set(values.filter(Boolean))];
  const isRepo = () => /^\/[^/]+\/[^/]+(?:\/(?:tree|blob)\/.*)?\/?$/.test(location.pathname);
  const isProfile = () => {
    const reserved = new Set(["settings", "marketplace", "explore", "topics", "collections", "orgs"]);
    const parts = location.pathname.split("/").filter(Boolean);
    return parts.length === 1 && !reserved.has(parts[0].toLowerCase());
  };
  const pageType = () => (isRepo() ? "github_repo" : "github_profile");
  const settings = async () => chrome.storage.local.get([
    "standaloneGeminiKey",
    "standaloneGeminiModel",
    "deepProjectAnalysis",
    "localToken",
    "useAI"
  ]);

  const captureProject = async () => {
    const saved = await settings();
    const deep = Boolean(saved.deepProjectAnalysis);
    const limit = deep ? 200 : 80;
    const parts = location.pathname.split("/").filter(Boolean);
    const links = [...document.querySelectorAll("a[href]")];
    const files = unique(links
      .map((anchor) => anchor.getAttribute("title") || anchor.getAttribute("href") || "")
      .filter((value) => /(^|\/)(README|src|app|modules|tests|docs|\.github|package\.json|pyproject\.toml|requirements\.txt|Dockerfile|docker-compose\.ya?ml)/i.test(value)))
      .slice(0, limit);
    const commits = unique([...document.querySelectorAll(
      "[data-testid*='commit'] a, [class*='commit'] a, a[href*='/commit/']"
    )].map(text)).slice(0, deep ? 100 : 30);
    const readme = text(document.querySelector("#readme, article.markdown-body, [data-testid='readme']"));
    const visible = text(document.querySelector("main") || document.body);
    return {
      url: location.href,
      owner: parts[0] || "",
      repo: isRepo() ? (parts[1] || "") : "",
      title: text(document.querySelector("h1")).replace(/SotuHire AI$/, "").trim() || document.title,
      page_type: pageType(),
      visible_text: visible.slice(0, deep ? 200000 : 100000),
      readme_text: readme.slice(0, deep ? 100000 : 50000),
      files_sampled: files,
      commit_messages: commits,
      languages: unique([...document.querySelectorAll("[aria-label*='language'], [class*='language']")].map(text)).slice(0, 100),
      topics: unique([...document.querySelectorAll("[data-octo-click*='topic'], [class*='topic']")].map(text)).slice(0, 100),
      provider_used: saved.useAI ? "gemini" : "local"
    };
  };

  const localRequest = async (path, body) => {
    const saved = await settings();
    const response = await fetch(`${API}${path}`, {
      method: body ? "POST" : "GET",
      headers: {
        "Content-Type": "application/json",
        "X-SotuHire-Token": saved.localToken || ""
      },
      body: body ? JSON.stringify(body) : undefined
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.message || `HTTP ${response.status}`);
    return payload;
  };

  const standalone = async (project) => {
    const saved = await settings();
    const report = globalThis.SotuHireProjectAnalyzer.analyze(project);
    report.provider_used = saved.standaloneGeminiKey ? "gemini-standalone" : "local-browser";
    if (!saved.standaloneGeminiKey) return report;
    const granted = await chrome.permissions.request({
      origins: ["https://generativelanguage.googleapis.com/*"]
    });
    if (!granted) throw new Error("Permissao do Gemini standalone nao concedida.");
    const model = saved.standaloneGeminiModel || "gemini-2.5-flash";
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-goog-api-key": saved.standaloneGeminiKey
        },
        body: JSON.stringify({
          contents: [{ parts: [{ text: `Aprimore sem inventar fatos:\n${JSON.stringify({ project, report })}` }] }]
        })
      }
    );
    if (!response.ok) throw new Error(`Gemini standalone falhou: HTTP ${response.status}`);
    const payload = await response.json();
    report.gemini_summary = payload.candidates?.[0]?.content?.parts?.[0]?.text || "";
    return report;
  };

  const scoreCard = (label, value) =>
    `<div class="metric"><span>${label}</span><strong>${value}/100</strong></div>`;
  const list = (items, empty) =>
    `<ul>${(items?.length ? items : [empty]).map((item) => `<li>${item}</li>`).join("")}</ul>`;
  const renderReport = (report) => `
    <section class="hero">
      <div class="score"><strong>${report.overall_score}</strong><span>/100</span></div>
      <div><span class="grade">Grade ${report.grade}</span><h2>${report.title || currentProject.title}</h2>
      <p>${report.summary}</p><small>Modelo: ${report.provider_used || "local"}</small></div>
    </section>
    <div class="badges">${(report.stack || []).map((item) => `<span>${item}</span>`).join("") || "<span>Stack nao detectada</span>"}</div>
    <section class="metrics">
      ${scoreCard("README", report.documentation_score)}
      ${scoreCard("Commits", report.commit_quality_score)}
      ${scoreCard("Arquitetura", report.architecture_signal_score)}
      ${scoreCard("Profundidade", report.technical_depth_score)}
      ${scoreCard("Manutencao", report.commit_analysis?.maintenance_signal_score || report.commit_quality_score)}
      ${scoreCard("Recrutador", report.recruiter_readiness_score)}
    </section>
    <section class="columns">
      <article><h3>Pontos fortes</h3>${list(report.strengths, "Nenhum sinal forte detectado.")}</article>
      <article><h3>Pontos fracos e inconsistencias</h3>${list(report.weaknesses, "Nenhuma inconsistencia relevante detectada.")}</article>
    </section>
    <article><h3>Recomendacoes por prioridade</h3>${list(report.priority_recommendations || report.risks, "Continue documentando evidencias verificaveis.")}</article>
    <article><h3>Evidencias para curriculo</h3>${list(report.resume_highlights, "Analise mais arquivos para gerar evidencias.")}</article>
    ${report.gemini_summary ? `<article><h3>Resumo Gemini</h3><p>${report.gemini_summary}</p></article>` : ""}
  `;

  const styles = `
    :host{all:initial;font-family:Inter,ui-sans-serif,system-ui;color:#f5f7fb}
    *{box-sizing:border-box}.backdrop{position:fixed;inset:0;z-index:2147483646;background:rgba(3,10,20,.72);backdrop-filter:blur(7px);display:grid;place-items:center;padding:24px}
    .modal{width:min(980px,96vw);max-height:92vh;overflow:hidden;border:1px solid #34506f;border-radius:18px;background:#071526;box-shadow:0 30px 90px #000b}
    header{display:flex;justify-content:space-between;align-items:center;padding:18px 22px;border-bottom:1px solid #263d57;background:#0b1d32}header strong{font-size:18px}button{cursor:pointer;border:1px solid #3c5878;border-radius:9px;padding:9px 13px;color:#f5f7fb;background:#142a44;font-weight:650}button:hover{border-color:#ff5369}.primary{background:#e83e5d;border-color:#ff5369}.close{font-size:20px;padding:3px 10px}.body{padding:20px;overflow:auto;max-height:calc(92vh - 136px)}
    .toolbar,.actions,.settings{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.settings{padding:12px;margin-bottom:16px;border:1px solid #29435f;border-radius:12px;background:#0b1d32}.settings input[type=text]{min-width:180px;padding:8px;border:1px solid #3c5878;border-radius:7px;background:#071526;color:#fff}.status{margin-left:auto;color:#9eb1ca}.hero{display:grid;grid-template-columns:auto 1fr;gap:20px;align-items:center;padding:18px;border:1px solid #29435f;border-radius:14px;background:linear-gradient(135deg,#102d4d,#0c1d32)}.hero h2{margin:7px 0}.hero p{color:#c8d3e2}.score{width:108px;height:108px;border-radius:50%;display:grid;place-content:center;text-align:center;border:9px solid #ff5369;background:#08192c}.score strong{font-size:34px}.score span{color:#9eb1ca}.grade{display:inline-block;border-radius:999px;background:#e83e5d;padding:4px 10px;font-weight:800}
    .badges{display:flex;gap:7px;flex-wrap:wrap;margin:14px 0}.badges span{padding:5px 9px;border-radius:999px;background:#163654;color:#b9d8ff}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.metric,article{border:1px solid #29435f;border-radius:12px;padding:13px;background:#0b1d32}.metric{display:flex;justify-content:space-between}.columns{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0}article{margin-top:10px}article h3{margin:0 0 8px;color:#d8e8ff}article li,article p{color:#c8d3e2;line-height:1.45}.loading,.error,.empty{padding:60px;text-align:center;color:#c8d3e2}.error{color:#ff9aaa}.actions{padding:15px 20px;border-top:1px solid #263d57;background:#0b1d32}
    @media(max-width:700px){.metrics,.columns{grid-template-columns:1fr}.hero{grid-template-columns:1fr}.score{width:86px;height:86px}}
  `;

  const modal = () => {
    document.getElementById(ROOT_ID)?.remove();
    const host = document.createElement("div");
    host.id = ROOT_ID;
    const shadow = host.attachShadow({ mode: "open" });
    shadow.innerHTML = `<style>${styles}</style><div class="backdrop"><div class="modal">
      <header><strong>SotuHire AI · GitHub Analyzer</strong><button class="close" data-action="close">×</button></header>
      <div class="body">
        <div class="settings">
          <label><input type="checkbox" data-setting="deepProjectAnalysis"> Deep analysis</label>
          <label><input type="checkbox" data-setting="useAI"> Usar Gemini pelo SotuHire</label>
          <input type="text" data-setting="standaloneGeminiModel" placeholder="Modelo Gemini">
          <span class="status">Verificando SotuHire local...</span>
        </div>
        <div class="report empty">Clique em analisar para gerar o relatorio publico.</div>
      </div>
      <div class="actions">
        <button class="primary" data-action="analyze">Analisar repositorio</button>
        <button data-action="save">Salvar no SotuHire</button>
        <button data-action="evidence">Usar como evidencia em vaga</button>
        <button data-action="memory">Enviar para memoria</button>
        <button data-action="profile">Enviar para perfil profissional</button>
        <button data-action="compare">Comparar com vaga atual</button>
        <button data-action="copy">Copiar resumo</button>
        <button data-action="export">Exportar relatorio</button>
      </div></div></div>`;
    document.documentElement.append(host);
    const query = (selector) => shadow.querySelector(selector);
    const reportNode = query(".report");
    settings().then((saved) => {
      query("[data-setting=deepProjectAnalysis]").checked = Boolean(saved.deepProjectAnalysis);
      query("[data-setting=useAI]").checked = Boolean(saved.useAI);
      query("[data-setting=standaloneGeminiModel]").value =
        saved.standaloneGeminiModel || "gemini-2.5-flash";
      localRequest("/health").then(() => {
        query(".status").textContent = "Connected SotuHire Mode recomendado";
      }).catch(() => {
        query(".status").textContent = saved.standaloneGeminiKey
          ? "Standalone Mode disponivel"
          : "SotuHire offline · configure a chave Gemini no popup";
      });
    });
    shadow.querySelectorAll("[data-setting]").forEach((input) => input.addEventListener("change", () => {
      chrome.storage.local.set({
        [input.dataset.setting]: input.type === "checkbox" ? input.checked : input.value
      });
    }));
    const runConnected = async (message) => {
      if (!currentProject) currentProject = await captureProject();
      reportNode.className = "report loading";
      reportNode.textContent = "Enviando somente sinais publicos para o SotuHire local...";
      const payload = await localRequest("/capture/repo-analysis", currentProject);
      currentReport = payload.report;
      reportNode.className = "report";
      reportNode.innerHTML = renderReport(currentReport);
      query(".status").textContent = message;
    };
    shadow.addEventListener("click", async (event) => {
      const action = event.target?.dataset?.action;
      if (!action) return;
      try {
        if (action === "close") return host.remove();
        if (action === "analyze") {
          reportNode.className = "report loading";
          reportNode.textContent = "Amostrando README, arquivos centrais e commits publicos...";
          currentProject = await captureProject();
          try {
            const connected = await localRequest("/capture/repo-analysis", currentProject);
            currentReport = connected.report;
          } catch (_error) {
            currentReport = await standalone(currentProject);
          }
          reportNode.className = "report";
          reportNode.innerHTML = renderReport(currentReport);
        }
        if (["save", "evidence", "memory", "profile", "compare"].includes(action)) {
          await runConnected("Relatorio e evidencias salvos no SotuHire.");
        }
        if (action === "copy") {
          if (!currentReport) throw new Error("Analise o repositorio primeiro.");
          await navigator.clipboard.writeText(currentReport.summary);
          query(".status").textContent = "Resumo copiado.";
        }
        if (action === "export") {
          if (!currentReport) throw new Error("Analise o repositorio primeiro.");
          const blob = new Blob([JSON.stringify(currentReport, null, 2)], {
            type: "application/json"
          });
          const anchor = document.createElement("a");
          anchor.href = URL.createObjectURL(blob);
          anchor.download = `sotuhire-${currentProject.repo || currentProject.owner || "report"}.json`;
          anchor.click();
          URL.revokeObjectURL(anchor.href);
        }
      } catch (error) {
        reportNode.className = "report error";
        reportNode.textContent = `Falha: ${error.message}`;
      }
    });
  };

  const injectButton = () => {
    if (!isRepo() && !isProfile()) return;
    const id = isRepo() ? "sotuhire-repo-button" : "sotuhire-profile-button";
    if (document.getElementById(id)) return;
    const button = document.createElement("button");
    button.id = id;
    button.type = "button";
    button.textContent = isRepo() ? "SotuHire AI" : "Analyze GitHub Profile with SotuHire";
    button.setAttribute("data-testid", "sotuhire-github-button");
    button.style.cssText = "margin-left:8px;padding:6px 12px;border:1px solid #ff5369;border-radius:7px;background:#e83e5d;color:#fff;font-weight:700;cursor:pointer";
    button.addEventListener("click", modal);
    const preferred = document.querySelector(
      "[data-testid='repository-actions'], .file-navigation, .Layout-sidebar h2, main h1"
    );
    const fallback = document.querySelector("main, [role='main'], body");
    (preferred || fallback)?.append(button);
  };

  const refresh = () => {
    if (lastPath !== location.pathname) {
      lastPath = location.pathname;
      document.getElementById("sotuhire-repo-button")?.remove();
      document.getElementById("sotuhire-profile-button")?.remove();
      document.getElementById(ROOT_ID)?.remove();
    }
    injectButton();
  };
  refresh();
  new MutationObserver(refresh).observe(document.documentElement, { childList: true, subtree: true });
})();
