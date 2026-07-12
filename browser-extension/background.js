/* SotuHire extension service worker: provider secrets, model catalogs and public GitHub enrichment. */

importScripts("project_analysis.js");

const COMPANION_API = "http://127.0.0.1:8765";
const APP_API = "http://127.0.0.1:8787/api/v1";
const CATALOG_MAX_AGE_MS = 6 * 60 * 60 * 1000;
const PROVIDERS = {
  local: {
    label: "Análise local",
    models: ["local-browser"],
    defaultModel: "local-browser",
  },
  sotuhire: {
    label: "IA configurada no SotuHire",
    models: ["configurado-no-sotuhire"],
    defaultModel: "configurado-no-sotuhire",
  },
  gemini: {
    label: "Google Gemini",
    models: ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
    defaultModel: "gemini-2.5-flash",
    keyUrl: "https://aistudio.google.com/app/apikey",
  },
  openai: {
    label: "OpenAI",
    models: ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"],
    defaultModel: "gpt-4.1-mini",
    keyUrl: "https://platform.openai.com/api-keys",
  },
};

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(["aiProvider"], (saved) => {
    if (!saved.aiProvider) {
      chrome.storage.local.set({
        aiProvider: "sotuhire",
        aiModels: {
          local: PROVIDERS.local.defaultModel,
          sotuhire: PROVIDERS.sotuhire.defaultModel,
          gemini: PROVIDERS.gemini.defaultModel,
          openai: PROVIDERS.openai.defaultModel,
        },
      });
    }
  });
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  handleMessage(message)
    .then((payload) => sendResponse({ ok: true, ...payload }))
    .catch((error) => sendResponse({ ok: false, error: safeError(error) }));
  return true;
});

async function handleMessage(message) {
  if (message.type === "SOTUHIRE_AI_STATUS") return aiStatus();
  if (message.type === "SOTUHIRE_AI_SAVE_KEY") {
    return saveProviderKey(
      message.provider,
      message.apiKey,
      Boolean(message.remember),
    );
  }
  if (message.type === "SOTUHIRE_AI_REMOVE_KEY")
    return removeProviderKey(message.provider);
  if (message.type === "SOTUHIRE_AI_LIST_MODELS") {
    return listModels(message.provider, Boolean(message.force));
  }
  if (message.type === "SOTUHIRE_AI_ANALYZE") {
    return analyzeProject(message.project, message.options || {});
  }
  if (message.type === "SOTUHIRE_GITHUB_ENRICH") {
    return {
      project: await enrichGitHubProject(
        message.project,
        Boolean(message.deep),
      ),
    };
  }
  throw new Error("Ação da extensão não reconhecida.");
}

async function aiStatus() {
  const saved = await chrome.storage.local.get([
    "aiProvider",
    "aiModels",
    "aiKeyPersistence",
  ]);
  const providers = {};
  for (const provider of ["gemini", "openai"]) {
    providers[provider] = {
      configured: Boolean(await getProviderKey(provider)),
      persistent: saved.aiKeyPersistence?.[provider] === "local",
      keyUrl: PROVIDERS[provider].keyUrl,
    };
  }
  return {
    provider: saved.aiProvider || "sotuhire",
    models: saved.aiModels || {},
    providers,
  };
}

async function saveProviderKey(provider, apiKey, remember) {
  requireExternalProvider(provider);
  const cleaned = String(apiKey || "").trim();
  if (cleaned.length < 12) throw new Error("A chave parece incompleta.");
  const keyName = secretName(provider);
  if (remember) {
    await persistentSecretSet(keyName, cleaned);
    await chrome.storage.session.remove([keyName]);
  } else {
    await chrome.storage.session.set({ [keyName]: cleaned });
    await persistentSecretDelete(keyName);
  }
  const saved = await chrome.storage.local.get(["aiKeyPersistence"]);
  await chrome.storage.local.set({
    aiProvider: provider,
    aiKeyPersistence: {
      ...(saved.aiKeyPersistence || {}),
      [provider]: remember ? "local" : "session",
    },
  });
  try {
    const models =
      provider === "gemini"
        ? await listGeminiModels(cleaned)
        : await listOpenAiModels(cleaned);
    if (!models.length)
      throw new Error("O provider não retornou modelos compatíveis.");
    const entry = { models, refreshedAt: new Date().toISOString() };
    const catalog = await chrome.storage.local.get(["aiModelCatalog"]);
    await chrome.storage.local.set({
      aiModelCatalog: { ...(catalog.aiModelCatalog || {}), [provider]: entry },
    });
    return {
      configured: true,
      persistent: remember,
      ...entry,
      source: "official",
    };
  } catch (error) {
    await chrome.storage.session.remove([keyName]);
    await persistentSecretDelete(keyName);
    throw error;
  }
}

async function removeProviderKey(provider) {
  requireExternalProvider(provider);
  const keyName = secretName(provider);
  await chrome.storage.session.remove([keyName]);
  await persistentSecretDelete(keyName);
  await chrome.storage.local.remove([keyName]); // Remove any value left by pre-v0.9.1 builds.
  return { configured: false };
}

async function getProviderKey(provider) {
  const keyName = secretName(provider);
  const session = await chrome.storage.session.get([keyName]);
  if (session[keyName]) return session[keyName];
  return persistentSecretGet(keyName);
}

async function persistentSecretGet(key) {
  if (!globalThis.indexedDB) return globalThis.__sotuhireTestVault?.[key] || "";
  const db = await openSecretVault();
  return new Promise((resolve, reject) => {
    const request = db
      .transaction("secrets", "readonly")
      .objectStore("secrets")
      .get(key);
    request.onsuccess = () => resolve(request.result || "");
    request.onerror = () =>
      reject(new Error("Não foi possível ler o cofre local da extensão."));
  });
}

async function persistentSecretSet(key, value) {
  if (!globalThis.indexedDB) {
    globalThis.__sotuhireTestVault = {
      ...(globalThis.__sotuhireTestVault || {}),
      [key]: value,
    };
    return;
  }
  const db = await openSecretVault();
  await new Promise((resolve, reject) => {
    const request = db
      .transaction("secrets", "readwrite")
      .objectStore("secrets")
      .put(value, key);
    request.onsuccess = () => resolve();
    request.onerror = () =>
      reject(new Error("Não foi possível salvar no cofre local da extensão."));
  });
}

async function persistentSecretDelete(key) {
  if (!globalThis.indexedDB) {
    if (globalThis.__sotuhireTestVault)
      delete globalThis.__sotuhireTestVault[key];
    return;
  }
  const db = await openSecretVault();
  await new Promise((resolve, reject) => {
    const request = db
      .transaction("secrets", "readwrite")
      .objectStore("secrets")
      .delete(key);
    request.onsuccess = () => resolve();
    request.onerror = () =>
      reject(new Error("Não foi possível limpar o cofre local da extensão."));
  });
}

function openSecretVault() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("sotuhire-extension-vault", 1);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains("secrets")) {
        request.result.createObjectStore("secrets");
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () =>
      reject(new Error("Não foi possível abrir o cofre local da extensão."));
  });
}

async function listModels(provider, force = false) {
  if (!PROVIDERS[provider]) throw new Error("Provider inválido.");
  if (["local", "sotuhire"].includes(provider)) {
    return {
      models: PROVIDERS[provider].models,
      source: "builtin",
      refreshedAt: "",
    };
  }
  const saved = await chrome.storage.local.get(["aiModelCatalog"]);
  const cached = saved.aiModelCatalog?.[provider];
  const fresh =
    cached && Date.now() - Date.parse(cached.refreshedAt) < CATALOG_MAX_AGE_MS;
  if (!force && fresh) return { ...cached, source: "cache" };
  const key = await getProviderKey(provider);
  if (!key) {
    return {
      models: cached?.models || PROVIDERS[provider].models,
      source: cached ? "cache" : "builtin",
      refreshedAt: cached?.refreshedAt || "",
      warning: "Configure a chave para consultar o catálogo oficial.",
    };
  }
  try {
    const models =
      provider === "gemini"
        ? await listGeminiModels(key)
        : await listOpenAiModels(key);
    const entry = {
      models: models.length ? models : PROVIDERS[provider].models,
      refreshedAt: new Date().toISOString(),
    };
    await chrome.storage.local.set({
      aiModelCatalog: { ...(saved.aiModelCatalog || {}), [provider]: entry },
    });
    return { ...entry, source: "official" };
  } catch (error) {
    return {
      models: cached?.models || PROVIDERS[provider].models,
      source: cached ? "cache" : "builtin",
      refreshedAt: cached?.refreshedAt || "",
      warning: `Catálogo oficial indisponível: ${safeError(error)}`,
    };
  }
}

async function listGeminiModels(key) {
  const response = await fetch(
    "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000",
    {
      headers: { "x-goog-api-key": key },
      credentials: "omit",
    },
  );
  const payload = await responseJson(response);
  return (payload.models || [])
    .filter((model) =>
      (model.supportedGenerationMethods || []).includes("generateContent"),
    )
    .map((model) => String(model.name || "").replace(/^models\//, ""))
    .filter(Boolean)
    .sort(modelSort);
}

async function listOpenAiModels(key) {
  const response = await fetch("https://api.openai.com/v1/models", {
    headers: { Authorization: `Bearer ${key}` },
    credentials: "omit",
  });
  const payload = await responseJson(response);
  return (payload.data || [])
    .map((model) => String(model.id || ""))
    .filter((id) => /^(gpt-(?:4|5)|o[134](?:-|$))/i.test(id))
    .filter(
      (id) =>
        !/(audio|image|realtime|transcribe|tts|search|embedding)/i.test(id),
    )
    .sort(modelSort);
}

async function analyzeProject(project, options) {
  const provider = options.provider || "local";
  const model =
    options.model || PROVIDERS[provider]?.defaultModel || "local-browser";
  const deep = Boolean(options.deep);
  const enriched = await enrichGitHubProject(project, deep);
  const localReport = globalThis.SotuHireProjectAnalyzer.analyze(enriched);
  const baseTrace = {
    provider_requested: provider,
    model_requested: model,
    prompt_id: "extension_github_portfolio_analysis_v2",
    prompt_version: "2.0.0",
    generated_at: new Date().toISOString(),
    source_refs: [enriched.url].filter(Boolean),
    needs_user_review: true,
  };
  if (provider === "local") {
    return {
      project: enriched,
      report: {
        ...localReport,
        ...baseTrace,
        provider_used: "local-browser",
        model_used: "local-browser",
        analysis_mode: "local",
        fallback_used: false,
        fallback_reason: "",
      },
    };
  }
  if (provider === "sotuhire") {
    return analyzeWithSotuHire(enriched, localReport, baseTrace);
  }
  requireExternalProvider(provider);
  const key = await getProviderKey(provider);
  if (!key)
    throw new Error(
      `Configure uma chave ${PROVIDERS[provider].label} na extensão.`,
    );
  try {
    const insights =
      provider === "gemini"
        ? await analyzeWithGemini(key, model, enriched, localReport)
        : await analyzeWithOpenAi(key, model, enriched, localReport);
    return {
      project: enriched,
      report: mergeAiInsights(localReport, insights, {
        ...baseTrace,
        provider_used: provider,
        model_used: model,
        analysis_mode: "ai",
        fallback_used: false,
        fallback_reason: "",
      }),
    };
  } catch (error) {
    return {
      project: enriched,
      warning: safeError(error),
      report: {
        ...localReport,
        ...baseTrace,
        provider_used: "local-browser",
        model_used: "local-browser",
        analysis_mode: "fallback",
        fallback_used: true,
        fallback_reason: safeError(error),
      },
    };
  }
}

async function analyzeWithSotuHire(project, localReport, trace) {
  if (project.page_type === "github_repo" && project.url) {
    try {
      const appResponse = await fetch(`${APP_API}/github/repo/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_url: project.url,
          mode: "full",
          fallback_payload: project,
          request_id: `extension-${Date.now()}`,
        }),
      });
      const appPayload = await responseJson(appResponse);
      const data = appPayload.data;
      if (data?.report) {
        const normalized = normalizeSotuHireReport(data.report);
        return {
          project,
          report: {
            ...normalized,
            ...trace,
            provider_requested:
              data.provider_requested || data.requested_provider || "local",
            provider_used:
              data.provider_used || normalized.provider_used || "local",
            model_requested: data.model_requested || "configurado-no-sotuhire",
            model_used: data.model_used || data.model || "local",
            prompt_id: data.prompt_id || trace.prompt_id,
            prompt_version: data.prompt_version || trace.prompt_version,
            analysis_mode: data.analysis_mode || "local",
            fallback_used: Boolean(data.fallback_used),
            fallback_reason: data.fallback_reason || "",
            source_refs: data.source_refs || trace.source_refs,
            evidence_used: data.evidence_used || [],
            needs_user_review: true,
          },
        };
      }
    } catch (_error) {
      // The legacy Companion remains the safe fallback when the web API is not running.
    }
  }
  const saved = await chrome.storage.local.get(["localToken"]);
  const response = await fetch(`${COMPANION_API}/capture/repo-analysis`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-SotuHire-Token": saved.localToken || "",
    },
    body: JSON.stringify({
      ...project,
      provider_used: "local",
      analysis_result: { ...(project.analysis_result || {}), use_ai: true },
    }),
  });
  const payload = await responseJson(response);
  const report = payload.report || localReport;
  return {
    project,
    report: {
      ...report,
      ...trace,
      provider_used: report.provider_used || "local",
      model_used: report.model_used || "configurado-no-sotuhire",
      analysis_mode:
        report.provider_used && !report.provider_used.startsWith("local")
          ? "ai"
          : "local",
      fallback_used: Boolean(report.fallback_used),
      fallback_reason: report.fallback_reason || "",
    },
  };
}

function normalizeSotuHireReport(report) {
  if (report.overall_score != null) return report;
  const scores = report.scores || {};
  const dimensions = report.dimension_scores || {};
  const stack = report.tech_stack || {};
  const identity = report.repository_identity || {};
  const resumeBullets = (report.resume_evidence?.safe_resume_bullets || [])
    .map((item) => item.bullet)
    .filter(Boolean);
  const architecture = report.architecture || {};
  return {
    ...report,
    title:
      [identity.owner, identity.name].filter(Boolean).join("/") ||
      "Repositório público",
    overall_score: scores.overall_score ?? 0,
    grade: scores.grade || "F",
    summary:
      report.executive_summary?.professional_summary ||
      report.executive_summary?.short_summary ||
      report.final_verdict?.one_sentence_verdict ||
      "Análise concluída pelo SotuHire.",
    documentation_score:
      scores.documentation_score ?? (dimensions.documentation || 0) * 10,
    commit_quality_score: (dimensions.consistency || 0) * 10,
    architecture_signal_score: (dimensions.architecture || 0) * 10,
    technical_depth_score:
      scores.technical_score ?? (dimensions.code_quality || 0) * 10,
    recruiter_readiness_score:
      scores.recruiter_readiness_score ??
      (dimensions.recruiter_readiness || 0) * 10,
    stack: [
      ...new Set([
        ...(stack.languages || []),
        ...(stack.frameworks || []),
        ...(stack.libraries || []),
        ...(stack.tools || []),
        ...(stack.databases || []),
        ...(stack.devops || []),
        ...(stack.testing_tools || []),
      ]),
    ],
    strengths: [
      ...(report.portfolio_value?.career_strengths || []),
      ...(architecture.positive_signals || []),
    ],
    weaknesses: [
      ...(report.portfolio_value?.career_weaknesses || []),
      ...(architecture.problems || []),
    ],
    priority_recommendations:
      report.recommendations || report.final_verdict?.next_3_actions || [],
    resume_highlights: resumeBullets,
    architecture_assessment: [architecture.rating, architecture.style]
      .filter(Boolean)
      .join(" · "),
    commit_analysis: {
      maintenance_signal_score: (dimensions.maintainability || 0) * 10,
    },
  };
}

async function analyzeWithGemini(key, model, project, localReport) {
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-goog-api-key": key },
      credentials: "omit",
      body: JSON.stringify({
        contents: [
          {
            role: "user",
            parts: [{ text: analysisPrompt(project, localReport) }],
          },
        ],
        generationConfig: { responseMimeType: "application/json" },
      }),
    },
  );
  const payload = await responseJson(response);
  const text = payload.candidates?.[0]?.content?.parts
    ?.map((part) => part.text || "")
    .join("");
  return parseAiJson(text);
}

async function analyzeWithOpenAi(key, model, project, localReport) {
  const response = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${key}`,
    },
    credentials: "omit",
    body: JSON.stringify({
      model,
      response_format: { type: "json_object" },
      input: [
        {
          role: "system",
          content:
            "Você é um revisor técnico evidence-first. Responda apenas JSON válido e não invente fatos.",
        },
        { role: "user", content: analysisPrompt(project, localReport) },
      ],
    }),
  });
  const payload = await responseJson(response);
  const text =
    payload.output_text ||
    (payload.output || [])
      .flatMap((item) => item.content || [])
      .map((item) => item.text || "")
      .join("");
  return parseAiJson(text);
}

function analysisPrompt(project, localReport) {
  const evidence = compactProject(project);
  return [
    "Analise este perfil/repositório/portfólio público do GitHub para qualidade técnica e carreira.",
    "Use SOMENTE as evidências fornecidas. Não invente tecnologias, impacto, autoria ou experiência.",
    "Os scores locais são determinísticos e não devem ser substituídos.",
    "Responda em pt-BR como JSON com as chaves:",
    "summary (string), architecture_assessment (string), strengths (string[]), weaknesses (string[]),",
    "inconsistencies (string[]), priority_recommendations (string[]), resume_highlights (string[]),",
    "stack (string[]), evidence (string[]), confidence (high|medium|low).",
    `EVIDÊNCIAS PÚBLICAS: ${JSON.stringify(evidence)}`,
    `ANÁLISE LOCAL: ${JSON.stringify(localReport)}`,
  ].join("\n");
}

function compactProject(project) {
  return {
    url: project.url,
    owner: project.owner,
    repo: project.repo,
    title: project.title,
    page_type: project.page_type,
    readme_text: String(project.readme_text || "").slice(0, 50000),
    visible_text: String(project.visible_text || "").slice(0, 30000),
    files_sampled: (project.files_sampled || []).slice(0, 200),
    commit_messages: (project.commit_messages || []).slice(0, 100),
    languages: (project.languages || []).slice(0, 100),
    topics: (project.topics || []).slice(0, 100),
    analysis_result: project.analysis_result || {},
  };
}

function mergeAiInsights(localReport, insights, trace) {
  const strings = (value) =>
    Array.isArray(value) ? value.map(String).filter(Boolean).slice(0, 20) : [];
  return {
    ...localReport,
    ...trace,
    summary: String(insights.summary || localReport.summary).slice(0, 5000),
    architecture_assessment: String(
      insights.architecture_assessment || "",
    ).slice(0, 5000),
    strengths: strings(insights.strengths).length
      ? strings(insights.strengths)
      : localReport.strengths,
    weaknesses: strings(insights.weaknesses).length
      ? strings(insights.weaknesses)
      : localReport.weaknesses,
    inconsistencies: strings(insights.inconsistencies),
    priority_recommendations: strings(insights.priority_recommendations).length
      ? strings(insights.priority_recommendations)
      : localReport.priority_recommendations,
    resume_highlights: strings(insights.resume_highlights).length
      ? strings(insights.resume_highlights)
      : localReport.resume_highlights,
    stack: [
      ...new Set([...(localReport.stack || []), ...strings(insights.stack)]),
    ].slice(0, 30),
    evidence_used: strings(insights.evidence),
    ai_confidence: ["high", "medium", "low"].includes(insights.confidence)
      ? insights.confidence
      : "low",
  };
}

async function enrichGitHubProject(project, deep) {
  if (!project || !String(project.url || "").startsWith("https://github.com/"))
    return project;
  const owner = String(project.owner || "").trim();
  const repo = String(project.repo || "").trim();
  if (!owner) return project;
  const analysis = {
    ...(project.analysis_result || {}),
    github_enrichment: "public-rest",
  };
  try {
    if (!repo || project.page_type === "github_profile") {
      const [profile, repositories] = await Promise.all([
        githubGet(`/users/${encodeURIComponent(owner)}`),
        githubGet(
          `/users/${encodeURIComponent(owner)}/repos?sort=updated&per_page=${deep ? 30 : 12}`,
        ),
      ]);
      return {
        ...project,
        title: profile.name || profile.login || project.title,
        visible_text: [
          project.visible_text,
          profile.bio,
          `Seguidores: ${profile.followers || 0}; seguindo: ${profile.following || 0}`,
          `Repositórios públicos: ${profile.public_repos || 0}`,
          ...repositories.map(
            (item) => `${item.name}: ${item.description || "sem descrição"}`,
          ),
        ]
          .filter(Boolean)
          .join("\n")
          .slice(0, 200000),
        languages: [
          ...new Set([
            ...(project.languages || []),
            ...repositories.map((item) => item.language).filter(Boolean),
          ]),
        ],
        topics: [
          ...new Set([
            ...(project.topics || []),
            ...repositories.flatMap((item) => item.topics || []),
          ]),
        ],
        analysis_result: {
          ...analysis,
          profile: {
            public_repos: profile.public_repos,
            followers: profile.followers,
            created_at: profile.created_at,
            updated_at: profile.updated_at,
          },
          repositories: repositories.map((item) => ({
            name: item.name,
            description: item.description,
            language: item.language,
            stars: item.stargazers_count,
            forks: item.forks_count,
            archived: item.archived,
            updated_at: item.updated_at,
            topics: item.topics || [],
          })),
        },
      };
    }
    const encoded = `${encodeURIComponent(owner)}/${encodeURIComponent(repo)}`;
    const [metadata, languages, commits, readme, tree] = await Promise.all([
      githubGet(`/repos/${encoded}`),
      githubGet(`/repos/${encoded}/languages`),
      githubGet(`/repos/${encoded}/commits?per_page=${deep ? 60 : 20}`),
      githubGet(`/repos/${encoded}/readme`, "raw").catch(() => ""),
      deep
        ? githubGet(`/repos/${encoded}/git/trees/HEAD?recursive=1`).catch(
            () => ({ tree: [] }),
          )
        : Promise.resolve({ tree: [] }),
    ]);
    const treePaths = (tree.tree || [])
      .filter((item) => item.type === "blob")
      .map((item) => item.path);
    const priorityFiles = treePaths
      .filter((path) =>
        /(^|\/)(README|src|app|modules|tests|docs|\.github)|(^|\/)(package\.json|pyproject\.toml|requirements.*\.txt|Dockerfile|docker-compose\.ya?ml)$/i.test(
          path,
        ),
      )
      .slice(0, 200);
    return {
      ...project,
      title: metadata.full_name || project.title,
      readme_text: String(readme || project.readme_text || "").slice(0, 100000),
      files_sampled: [
        ...new Set([...(project.files_sampled || []), ...priorityFiles]),
      ].slice(0, 200),
      commit_messages: [
        ...new Set([
          ...(project.commit_messages || []),
          ...commits.map((item) => item.commit?.message).filter(Boolean),
        ]),
      ].slice(0, 200),
      languages: [
        ...new Set([
          ...(project.languages || []),
          ...Object.keys(languages || {}),
        ]),
      ],
      topics: [
        ...new Set([...(project.topics || []), ...(metadata.topics || [])]),
      ],
      analysis_result: {
        ...analysis,
        use_github_api: true,
        repository: {
          description: metadata.description,
          stars: metadata.stargazers_count,
          forks: metadata.forks_count,
          issues: metadata.open_issues_count,
          archived: metadata.archived,
          license: metadata.license?.spdx_id || "",
          default_branch: metadata.default_branch,
          created_at: metadata.created_at,
          updated_at: metadata.updated_at,
          pushed_at: metadata.pushed_at,
          size: metadata.size,
        },
        language_bytes: languages,
      },
    };
  } catch (error) {
    return {
      ...project,
      analysis_result: {
        ...analysis,
        github_enrichment_error: safeError(error),
      },
    };
  }
}

async function githubGet(path, mode = "json") {
  const headers = {
    Accept:
      mode === "raw"
        ? "application/vnd.github.raw+json"
        : "application/vnd.github+json",
  };
  const response = await fetch(`https://api.github.com${path}`, {
    headers,
    credentials: "omit",
  });
  if (!response.ok) throw new Error(`GitHub público: HTTP ${response.status}`);
  return mode === "raw" ? response.text() : response.json();
}

async function responseJson(response) {
  let payload;
  try {
    payload = await response.json();
  } catch (_error) {
    throw new Error(
      `Provider retornou HTTP ${response.status} sem JSON válido.`,
    );
  }
  if (!response.ok) {
    throw new Error(
      payload.error?.message || payload.message || `HTTP ${response.status}`,
    );
  }
  return payload;
}

function parseAiJson(value) {
  const cleaned = String(value || "")
    .trim()
    .replace(/^```(?:json)?/i, "")
    .replace(/```$/, "")
    .trim();
  if (!cleaned) throw new Error("Provider não retornou conteúdo analisável.");
  try {
    return JSON.parse(cleaned);
  } catch (_error) {
    throw new Error(
      "Provider retornou JSON inválido; análise local preservada.",
    );
  }
}

function secretName(provider) {
  requireExternalProvider(provider);
  return `sotuhireExtensionSecret_${provider}`;
}

function requireExternalProvider(provider) {
  if (!PROVIDERS[provider] || ["local", "sotuhire"].includes(provider)) {
    throw new Error("Provider externo inválido.");
  }
}

function modelSort(left, right) {
  return right.localeCompare(left, undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

function safeError(error) {
  return String(error?.message || error || "Falha desconhecida.")
    .replace(/AIza[0-9A-Za-z_-]+|sk-[A-Za-z0-9_-]+/g, "[secret]")
    .slice(0, 500);
}
