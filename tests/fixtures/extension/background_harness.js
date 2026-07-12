const path = require("node:path");

const extensionRoot = path.resolve(process.argv[2]);
const stores = { local: {}, session: {} };
const calls = [];
let listener;

const storageArea = (name) => ({
  async get(keys) {
    const selected = Array.isArray(keys) ? keys : Object.keys(stores[name]);
    return Object.fromEntries(selected.map((key) => [key, stores[name][key]]));
  },
  async set(payload) {
    Object.assign(stores[name], payload);
  },
  async remove(keys) {
    for (const key of keys) delete stores[name][key];
  },
});

global.chrome = {
  storage: { local: storageArea("local"), session: storageArea("session") },
  runtime: {
    onInstalled: { addListener() {} },
    onMessage: {
      addListener(callback) {
        listener = callback;
      },
    },
  },
};
global.importScripts = (...files) =>
  files.forEach((file) => require(path.join(extensionRoot, file)));
global.fetch = async (url, options = {}) => {
  const body = options.body ? JSON.parse(options.body) : null;
  calls.push({
    url: String(url),
    model: body?.model,
    hasGeminiHeader: Boolean(options.headers?.["x-goog-api-key"]),
  });
  if (String(url).includes("/models?pageSize")) {
    return response({
      models: [
        {
          name: "models/gemini-new-test",
          supportedGenerationMethods: ["generateContent"],
        },
      ],
    });
  }
  if (String(url).endsWith("/v1/models")) {
    return response({ data: [{ id: "gpt-new-test" }, { id: "gpt-4.1-mini" }] });
  }
  if (String(url).includes(":generateContent")) {
    return response({
      candidates: [
        {
          content: { parts: [{ text: JSON.stringify(aiInsights("Gemini")) }] },
        },
      ],
    });
  }
  if (String(url).endsWith("/responses")) {
    return response({ output_text: JSON.stringify(aiInsights("OpenAI")) });
  }
  throw new Error(`Unexpected URL: ${url}`);
};

function response(payload, status = 200) {
  return {
    ok: status < 400,
    status,
    async json() {
      return payload;
    },
    async text() {
      return JSON.stringify(payload);
    },
  };
}

function aiInsights(provider) {
  return {
    summary: `${provider} analisou evidências públicas.`,
    architecture_assessment: "Estrutura modular detectada.",
    strengths: ["Testes presentes"],
    weaknesses: [],
    inconsistencies: [],
    priority_recommendations: ["Documentar decisões"],
    resume_highlights: ["Projeto público revisável"],
    stack: ["JavaScript"],
    evidence: ["README público"],
    confidence: "high",
  };
}

function send(message) {
  return new Promise((resolve) => listener(message, {}, resolve));
}

async function main() {
  require(path.join(extensionRoot, "background.js"));
  await send({
    type: "SOTUHIRE_AI_SAVE_KEY",
    provider: "gemini",
    apiKey: "fake-gemini-key-for-test",
    remember: false,
  });
  const gemini = await send({
    type: "SOTUHIRE_AI_ANALYZE",
    project: project(),
    options: { provider: "gemini", model: "gemini-new-test", deep: false },
  });
  await send({
    type: "SOTUHIRE_AI_SAVE_KEY",
    provider: "openai",
    apiKey: "fake-openai-key-for-test",
    remember: true,
  });
  const openai = await send({
    type: "SOTUHIRE_AI_ANALYZE",
    project: project(),
    options: { provider: "openai", model: "gpt-4.1-mini", deep: false },
  });
  console.log(
    JSON.stringify({
      geminiProvider: gemini.report.provider_used,
      geminiModel: gemini.report.model_used,
      openaiProvider: openai.report.provider_used,
      openaiModel: openai.report.model_used,
      sessionKeyCount: Object.keys(stores.session).length,
      vaultKeyCount: Object.keys(global.__sotuhireTestVault || {}).length,
      localSecretCount: Object.keys(stores.local).filter((key) =>
        key.includes("Secret"),
      ).length,
      calls,
    }),
  );
}

function project() {
  return {
    url: "https://example.invalid/project",
    title: "Projeto fictício",
    page_type: "project",
    readme_text: "Projeto com testes.",
    files_sampled: ["README.md", "tests/example.js"],
    commit_messages: ["feat: add example"],
    languages: ["JavaScript"],
    topics: ["testing"],
    analysis_result: {},
    provider_used: "local",
  };
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
