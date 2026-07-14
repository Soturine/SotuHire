(() => {
  const API = "http://127.0.0.1:8765";
  const ROOT_ID = "sotuhire-github-companion";
  let lastPath = "";
  let currentProject = null;
  let currentReport = null;

  const text = (element) =>
    (element?.innerText || "").replace(/\s+/g, " ").trim();
  const unique = (values) => [...new Set(values.filter(Boolean))];
  const isRepo = () =>
    /^\/[^/]+\/[^/]+(?:\/(?:tree|blob)\/.*)?\/?$/.test(location.pathname);
  const isProfile = () => {
    const reserved = new Set([
      "settings",
      "marketplace",
      "explore",
      "topics",
      "collections",
      "orgs",
    ]);
    const parts = location.pathname.split("/").filter(Boolean);
    return parts.length === 1 && !reserved.has(parts[0].toLowerCase());
  };
  const pageType = () => (isRepo() ? "github_repo" : "github_profile");
  const settings = async () =>
    chrome.storage.local.get([
      "deepProjectAnalysis",
      "localToken",
      "aiProvider",
      "aiModels",
    ]);

  const backgroundRequest = async (message) => {
    const response = await chrome.runtime.sendMessage(message);
    if (!response?.ok)
      throw new Error(response?.error || "A extensão não respondeu.");
    return response;
  };

  const captureProject = async () => {
    const saved = await settings();
    const deep = Boolean(saved.deepProjectAnalysis);
    const limit = deep ? 200 : 80;
    const parts = location.pathname.split("/").filter(Boolean);
    const links = [...document.querySelectorAll("a[href]")];
    const files = unique(
      links
        .map(
          (anchor) =>
            anchor.getAttribute("title") || anchor.getAttribute("href") || "",
        )
        .filter((value) =>
          /(^|\/)(README|src|app|modules|tests|docs|\.github|package\.json|pyproject\.toml|requirements\.txt|Dockerfile|docker-compose\.ya?ml)/i.test(
            value,
          ),
        ),
    ).slice(0, limit);
    const commits = unique(
      [
        ...document.querySelectorAll(
          "[data-testid*='commit'] a, [class*='commit'] a, a[href*='/commit/']",
        ),
      ].map(text),
    ).slice(0, deep ? 100 : 30);
    const readme = text(
      document.querySelector(
        "#readme, article.markdown-body, [data-testid='readme']",
      ),
    );
    const visible = text(document.querySelector("main") || document.body);
    return {
      url: location.href,
      owner: parts[0] || "",
      repo: isRepo() ? parts[1] || "" : "",
      title:
        text(document.querySelector("h1"))
          .replace(/SotuHire AI$/, "")
          .trim() || document.title,
      page_type: pageType(),
      visible_text: visible.slice(0, deep ? 200000 : 100000),
      readme_text: readme.slice(0, deep ? 100000 : 50000),
      files_sampled: files,
      commit_messages: commits,
      languages: unique(
        [
          ...document.querySelectorAll(
            "[aria-label*='language'], [class*='language']",
          ),
        ].map(text),
      ).slice(0, 100),
      topics: unique(
        [
          ...document.querySelectorAll(
            "[data-octo-click*='topic'], [class*='topic']",
          ),
        ].map(text),
      ).slice(0, 100),
      analysis_result: {
        use_github_api: pageType() === "github_repo",
        use_ai: saved.aiProvider === "sotuhire",
      },
      provider_used: "local",
    };
  };

  const localRequest = async (path, body) => {
    const saved = await settings();
    const response = await fetch(`${API}${path}`, {
      method: body ? "POST" : "GET",
      headers: {
        "Content-Type": "application/json",
        "X-SotuHire-Token": saved.localToken || "",
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    const payload = await response.json();
    if (!response.ok)
      throw new Error(payload.message || `HTTP ${response.status}`);
    return payload;
  };

  const standalone = async (project, provider, model) => {
    const payload = await backgroundRequest({
      type: "SOTUHIRE_AI_ANALYZE",
      project,
      options: {
        provider,
        model,
        deep: Boolean((await settings()).deepProjectAnalysis),
      },
    });
    currentProject = payload.project;
    return payload.report;
  };

  const escapeHtml = (value) =>
    String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  const scoreCard = (label, value) =>
    `<div class="metric"><span>${escapeHtml(label)}</span><strong>${Number(value) || 0}/100</strong></div>`;
  const list = (items, empty) =>
    `<ul>${(items?.length ? items : [empty]).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  const feedbackControls = (report) =>
    report.run_id
      ? `<article class="feedback"><h3>Este resultado ajudou?</h3><p>O feedback envia apenas o identificador do trace e sua avaliação; nenhum conteúdo do GitHub ou chave é incluído.</p><div class="feedback-buttons">
          <button data-action="feedback" data-rating="useful" data-decision="accepted">Útil e aceito</button>
          <button data-action="feedback" data-rating="partial" data-decision="edited">Útil após editar</button>
          <button data-action="feedback" data-rating="not_useful" data-decision="rejected">Não útil</button>
          <button data-action="feedback" data-rating="partial" data-decision="rejected" data-unsupported-claim="true">Afirmação sem evidência</button>
        </div></article>`
      : `<article class="feedback"><h3>Feedback</h3><p>Conecte a análise à IA do SotuHire para registrar feedback vinculado a um trace seguro.</p></article>`;
  const renderReport = (report) => `
    <section class="hero">
      <div class="score"><strong>${report.overall_score}</strong><span>/100</span></div>
      <div><span class="grade">Grade ${escapeHtml(report.grade)}</span><h2>${escapeHtml(report.title || currentProject.title)}</h2>
      <p>${escapeHtml(report.summary)}</p><small>${escapeHtml(report.provider_used || "local")} · ${escapeHtml(report.model_used || "local-browser")}${report.fallback_used ? " · fallback local" : ""}</small></div>
    </section>
    <div class="badges">${(report.stack || []).map((item) => `<span>${escapeHtml(item)}</span>`).join("") || "<span>Stack não detectada</span>"}</div>
    ${report.architecture_assessment ? `<article class="architecture"><h3>Arquitetura</h3><p>${escapeHtml(report.architecture_assessment)}</p></article>` : ""}
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
      <article><h3>Pontos fracos</h3>${list(report.weaknesses, "Nenhum ponto fraco relevante detectado.")}</article>
    </section>
    <article><h3>Inconsistências</h3>${list(report.inconsistencies, "Nenhuma inconsistência sustentada pelas evidências.")}</article>
    <article><h3>Recomendações por prioridade</h3>${list(report.priority_recommendations || report.risks, "Continue documentando evidências verificáveis.")}</article>
    <article><h3>Evidências para currículo</h3>${list(report.resume_highlights, "Analise mais arquivos para gerar evidências.")}</article>
    <article><h3>Rastreabilidade</h3><p>Prompt ${escapeHtml(report.prompt_id || "análise local")} · versão ${escapeHtml(report.prompt_version || "local")} · revisão humana obrigatória.</p></article>
    ${feedbackControls(report)}
  `;

  const styles = `
    :host{all:initial;font-family:Inter,ui-sans-serif,system-ui;color:#f5f7fb}
    *{box-sizing:border-box}.backdrop{position:fixed;inset:0;z-index:2147483646;background:rgba(3,10,20,.72);backdrop-filter:blur(7px);display:grid;place-items:center;padding:24px}
    .modal{width:min(980px,96vw);max-height:92vh;overflow:hidden;border:1px solid #34506f;border-radius:18px;background:#071526;box-shadow:0 30px 90px #000b}
    header{display:flex;justify-content:space-between;align-items:center;padding:18px 22px;border-bottom:1px solid #263d57;background:#081625}header strong{font-size:18px}button,select{font:inherit}button{cursor:pointer;border:1px solid #3c5878;border-radius:9px;padding:9px 13px;color:#f5f7fb;background:#142a44;font-weight:650}button:hover{border-color:#31d2ad}.primary{background:linear-gradient(135deg,#22cda9,#10927d);border-color:#31d2ad;color:#031f19}.close{font-size:20px;padding:3px 10px}.body{padding:20px;overflow:auto;max-height:calc(92vh - 136px)}
    .toolbar,.actions,.settings{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.settings{padding:12px;margin-bottom:16px;border:1px solid #29435f;border-radius:12px;background:#0b1d32}.settings label{display:grid;gap:4px;color:#aebed1;font-size:11px}.settings select{min-width:175px;padding:8px;border:1px solid #3c5878;border-radius:7px;background:#071526;color:#fff}.toggle{display:flex!important;grid-template-columns:auto 1fr!important;align-items:center}.status{margin-left:auto;color:#9eb1ca}.hero{display:grid;grid-template-columns:auto 1fr;gap:20px;align-items:center;padding:18px;border:1px solid #29435f;border-radius:14px;background:linear-gradient(135deg,#102d4d,#0c1d32)}.hero h2{margin:7px 0}.hero p{color:#c8d3e2}.score{width:108px;height:108px;border-radius:50%;display:grid;place-content:center;text-align:center;border:9px solid #24c9a7;background:#08192c}.score strong{font-size:34px}.score span{color:#9eb1ca}.grade{display:inline-block;border-radius:999px;background:#176d5e;padding:4px 10px;font-weight:800}
    .badges{display:flex;gap:7px;flex-wrap:wrap;margin:14px 0}.badges span{padding:5px 9px;border-radius:999px;background:#163654;color:#b9d8ff}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.metric,article{border:1px solid #29435f;border-radius:12px;padding:13px;background:#0b1d32}.metric{display:flex;justify-content:space-between}.columns{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0}article{margin-top:10px}article h3{margin:0 0 8px;color:#d8e8ff}article li,article p{color:#c8d3e2;line-height:1.45}.feedback-buttons{display:flex;gap:8px;flex-wrap:wrap}.loading,.error,.empty{padding:60px;text-align:center;color:#c8d3e2}.error{color:#ff9aaa}.actions{padding:15px 20px;border-top:1px solid #263d57;background:#0b1d32}
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
          <label>Provider<select data-setting="aiProvider">
            <option value="sotuhire">IA do SotuHire</option>
            <option value="gemini">Gemini da extensão</option>
            <option value="openai">OpenAI da extensão</option>
            <option value="local">Local sem chave</option>
          </select></label>
          <label>Modelo<select data-setting="aiModel"></select></label>
          <label class="toggle"><input type="checkbox" data-setting="deepProjectAnalysis"> Deep analysis</label>
          <span class="status">Verificando SotuHire local...</span>
        </div>
        <div class="report empty">Clique em analisar para revisar README, commits, arquitetura, stack e evidências públicas.</div>
      </div>
      <div class="actions">
        <button class="primary" data-action="analyze">✦ Analisar com o modelo selecionado</button>
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
    const loadModels = async (provider, selected = "") => {
      const payload = await backgroundRequest({
        type: "SOTUHIRE_AI_LIST_MODELS",
        provider,
        force: false,
      });
      const modelSelect = query("[data-setting=aiModel]");
      const models = [
        ...new Set([selected, ...(payload.models || [])].filter(Boolean)),
      ];
      modelSelect.replaceChildren(
        ...models.map((model) => new Option(model, model)),
      );
      modelSelect.value = selected || models[0] || "";
      query(".status").textContent =
        payload.warning || `${models.length} modelo(s) disponível(is)`;
    };
    settings().then(async (saved) => {
      query("[data-setting=deepProjectAnalysis]").checked = Boolean(
        saved.deepProjectAnalysis,
      );
      query("[data-setting=aiProvider]").value = saved.aiProvider || "sotuhire";
      await loadModels(
        saved.aiProvider || "sotuhire",
        saved.aiModels?.[saved.aiProvider || "sotuhire"],
      );
      localRequest("/health")
        .then(() => {
          query(".status").textContent += " · SotuHire conectado";
        })
        .catch(() => {
          query(".status").textContent += " · SotuHire offline";
        });
    });
    shadow.querySelectorAll("[data-setting]").forEach((input) =>
      input.addEventListener("change", async () => {
        if (input.dataset.setting === "aiModel") {
          const saved = await settings();
          await chrome.storage.local.set({
            aiModels: {
              ...(saved.aiModels || {}),
              [query("[data-setting=aiProvider]").value]: input.value,
            },
          });
          return;
        }
        await chrome.storage.local.set({
          [input.dataset.setting]:
            input.type === "checkbox" ? input.checked : input.value,
        });
        if (input.dataset.setting === "aiProvider") {
          const saved = await settings();
          await loadModels(input.value, saved.aiModels?.[input.value]);
        }
      }),
    );
    const runConnected = async (message) => {
      if (!currentProject) currentProject = await captureProject();
      reportNode.className = "report loading";
      reportNode.textContent =
        "Enviando somente sinais publicos para o SotuHire local...";
      const payload = await localRequest("/capture/repo-analysis", {
        ...currentProject,
        provider_used: "local",
        analysis_result: {
          ...(currentProject.analysis_result || {}),
          extension_ai_report: currentReport || null,
          use_ai: query("[data-setting=aiProvider]").value === "sotuhire",
        },
      });
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
          reportNode.textContent =
            "Coletando README, arquivos, commits e sinais públicos...";
          currentProject = await captureProject();
          const provider = query("[data-setting=aiProvider]").value;
          const model = query("[data-setting=aiModel]").value;
          currentReport = await standalone(currentProject, provider, model);
          reportNode.className = "report";
          reportNode.innerHTML = renderReport(currentReport);
        }
        if (action === "feedback") {
          if (!currentReport?.run_id)
            throw new Error("Este resultado não possui um trace do SotuHire.");
          await backgroundRequest({
            type: "SOTUHIRE_AI_FEEDBACK",
            feedback: {
              run_id: currentReport.run_id,
              task_id: currentReport.task_id || "github_repo_analysis",
              rating: event.target.dataset.rating,
              decision: event.target.dataset.decision,
              unsupported_claim:
                event.target.dataset.unsupportedClaim === "true",
            },
          });
          query(".status").textContent = "Feedback registrado com segurança.";
        }
        if (
          ["save", "evidence", "memory", "profile", "compare"].includes(action)
        ) {
          await runConnected("Relatorio e evidencias salvos no SotuHire.");
        }
        if (action === "copy") {
          if (!currentReport)
            throw new Error("Analise o repositorio primeiro.");
          await navigator.clipboard.writeText(currentReport.summary);
          query(".status").textContent = "Resumo copiado.";
        }
        if (action === "export") {
          if (!currentReport)
            throw new Error("Analise o repositorio primeiro.");
          const blob = new Blob([JSON.stringify(currentReport, null, 2)], {
            type: "application/json",
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
    button.textContent = isRepo()
      ? "✦ SotuHire Insight"
      : "✦ Analisar perfil com SotuHire";
    button.setAttribute("data-testid", "sotuhire-github-button");
    button.style.cssText =
      "margin-left:8px;padding:7px 13px;border:1px solid #35d8b4;border-radius:9px;background:linear-gradient(135deg,#1fbf9f,#107e6d);color:#031d18;font-weight:750;cursor:pointer;box-shadow:0 5px 18px #0fa08133";
    button.addEventListener("click", modal);
    const preferred = document.querySelector(
      "[data-testid='repository-actions'], .file-navigation, .Layout-sidebar h2, main h1",
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
  new MutationObserver(refresh).observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
})();
