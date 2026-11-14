/* Adversarial message checks for the extension service worker (synthetic, offline). */
const path = require("node:path");

const extensionRoot = path.resolve(process.argv[2]);
const stores = {
  local: {},
  session: {
    companionSessionToken: "synthetic-session-token",
    companionSessionExpiresAt: Date.now() + 60_000,
  },
};
const fetched = [];
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
    id: "test-extension-id",
    getURL: (file = "") => `chrome-extension://test-extension-id/${file}`,
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
  fetched.push({ url: String(url), token: options.headers?.["X-SotuHire-Token"] || "" });
  return { ok: true, status: 200, json: async () => ({ ok: true, status: "ok" }) };
};

const POPUP = { id: "test-extension-id", url: "chrome-extension://test-extension-id/popup.html" };
const CONTENT_SCRIPT = {
  id: "test-extension-id",
  url: "https://github.com/example/repo",
  tab: { id: 7 },
};
const OTHER_EXTENSION = { id: "another-extension", url: "chrome-extension://another-extension/x" };

function send(message, sender) {
  return new Promise((resolve) => listener(message, sender, resolve));
}

async function main() {
  require(path.join(extensionRoot, "background.js"));
  const results = {};
  for (const [name, path] of Object.entries({
    userinfoHost: "@attacker.invalid/steal",
    absoluteUrl: "https://attacker.invalid/steal",
    protocolRelative: "//attacker.invalid/steal",
    traversal: "/capture/../../admin",
    unknownRoute: "/admin/export",
  })) {
    const response = await send(
      { type: "SOTUHIRE_COMPANION_REQUEST", path, body: {} },
      CONTENT_SCRIPT,
    );
    results[name] = response.ok;
  }
  results.allowedRoute = (
    await send({ type: "SOTUHIRE_COMPANION_REQUEST", path: "/health" }, CONTENT_SCRIPT)
  ).ok;
  results.saveKeyFromContentScript = (
    await send(
      { type: "SOTUHIRE_AI_SAVE_KEY", provider: "gemini", apiKey: "x".repeat(20) },
      CONTENT_SCRIPT,
    )
  ).ok;
  results.removeKeyFromContentScript = (
    await send({ type: "SOTUHIRE_AI_REMOVE_KEY", provider: "gemini" }, CONTENT_SCRIPT)
  ).ok;
  results.pairFromContentScript = (
    await send({ type: "SOTUHIRE_COMPANION_PAIR" }, CONTENT_SCRIPT)
  ).ok;
  results.statusFromOtherExtension = (
    await send({ type: "SOTUHIRE_AI_STATUS" }, OTHER_EXTENSION)
  ).ok;
  results.statusFromPopup = (await send({ type: "SOTUHIRE_AI_STATUS" }, POPUP)).ok;
  const host = (url) => {
    try {
      return new URL(url).host;
    } catch {
      return `unparseable:${url}`;
    }
  };
  results.fetchedHosts = [...new Set(fetched.map((call) => host(call.url)))];
  results.tokenSentOutsideLoopback = fetched.some(
    (call) => call.token && host(call.url) !== "127.0.0.1:8765",
  );
  console.log(JSON.stringify(results));
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
