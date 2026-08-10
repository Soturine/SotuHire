const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const PAIRING_FRAGMENT_KEY = "sotuhire-pairing";

interface OriginPairingState {
  csrfToken: string;
  pairingPromise: Promise<void> | null;
}

const pairingByOrigin = new Map<string, OriginPairingState>();
let bootstrapRead = false;
let pairingBootstrap = "";

export function normalizeLocalApiBaseUrl(value: string): string {
  let parsed: URL;
  try {
    parsed = new URL(value.trim());
  } catch {
    throw new Error("Informe uma URL valida para a API local.");
  }
  const host = parsed.hostname.toLowerCase();
  if (
    !["http:", "https:"].includes(parsed.protocol) ||
    !["127.0.0.1", "localhost", "[::1]", "::1"].includes(host) ||
    parsed.username ||
    parsed.password ||
    parsed.search ||
    parsed.hash
  ) {
    throw new Error("A API Real deve usar uma URL HTTP(S) de loopback sem credenciais.");
  }
  const pathname = parsed.pathname.replace(/\/+$/, "");
  if (pathname && pathname !== "/api/v1") {
    throw new Error("A URL da API local deve terminar em /api/v1.");
  }
  return `${parsed.origin}/api/v1`;
}

export async function pairedApiFetch(
  baseUrl: string,
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const normalized = normalizeLocalApiBaseUrl(baseUrl);
  const first = await fetchWithSession(normalized, path, init);
  if (first.status !== 401) return first;
  if (await refreshCsrf(normalized)) {
    const refreshed = await fetchWithSession(normalized, path, init);
    if (refreshed.status !== 401) return refreshed;
  }
  await pairLocalApi(normalized);
  return fetchWithSession(normalized, path, init);
}

export function pairLocalApi(baseUrl: string): Promise<void> {
  const normalized = normalizeLocalApiBaseUrl(baseUrl);
  const state = stateFor(normalized);
  state.pairingPromise ??= exchangePairing(normalized).finally(() => {
    state.pairingPromise = null;
  });
  return state.pairingPromise;
}

export function clearInMemoryPairing(): void {
  pairingByOrigin.clear();
  pairingBootstrap = "";
  bootstrapRead = false;
}

async function exchangePairing(baseUrl: string): Promise<void> {
  const bootstrap = readPairingBootstrap();
  if (!bootstrap) {
    throw new Error("Reabra o SotuHire pelo launcher local para autorizar esta janela.");
  }
  const apiRoot = apiOrigin(baseUrl);
  const start = await fetch(`${apiRoot}/api/v1/security/pairing/start`, {
    method: "POST",
    credentials: "include",
    headers: {
      "content-type": "application/json",
      "X-SotuHire-Pairing-Bootstrap": bootstrap,
    },
    body: JSON.stringify({ client_kind: "web", client_name: "SotuHire Web" }),
  });
  const challenge = await responseData(start);
  const complete = await fetch(`${apiRoot}/api/v1/security/pairing/complete`, {
    method: "POST",
    credentials: "include",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      challenge_id: challenge.challenge_id,
      proof: challenge.proof,
      client_kind: "web",
    }),
  });
  const paired = await responseData(complete);
  const csrfToken = String(paired.csrf_token || "");
  if (!csrfToken) throw new Error("O pareamento local nao retornou protecao CSRF.");
  stateFor(baseUrl).csrfToken = csrfToken;
  pairingBootstrap = "";
}

async function refreshCsrf(baseUrl: string): Promise<boolean> {
  const response = await fetch(`${apiOrigin(baseUrl)}/api/v1/security/csrf`, {
    method: "GET",
    credentials: "include",
  });
  if (!response.ok) return false;
  const paired = await responseData(response);
  const csrfToken = String(paired.csrf_token || "");
  if (!csrfToken) return false;
  stateFor(baseUrl).csrfToken = csrfToken;
  return true;
}

async function fetchWithSession(
  baseUrl: string,
  path: string,
  init: RequestInit,
): Promise<Response> {
  const method = String(init.method || "GET").toUpperCase();
  const csrfToken = stateFor(baseUrl).csrfToken;
  return fetch(`${baseUrl.replace(/\/+$/, "")}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(MUTATING_METHODS.has(method) && csrfToken ? { "X-SotuHire-CSRF": csrfToken } : {}),
      ...(init.headers ?? {}),
    },
  });
}

function stateFor(baseUrl: string): OriginPairingState {
  const origin = apiOrigin(baseUrl);
  let state = pairingByOrigin.get(origin);
  if (!state) {
    state = { csrfToken: "", pairingPromise: null };
    pairingByOrigin.set(origin, state);
  }
  return state;
}

function apiOrigin(baseUrl: string): string {
  return new URL(normalizeLocalApiBaseUrl(baseUrl)).origin;
}

function readPairingBootstrap(): string {
  if (bootstrapRead || typeof window === "undefined") return pairingBootstrap;
  bootstrapRead = true;
  const fragment = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  pairingBootstrap = fragment.get(PAIRING_FRAGMENT_KEY)?.trim() || "";
  if (pairingBootstrap) {
    window.history.replaceState(
      window.history.state,
      document.title,
      `${window.location.pathname}${window.location.search}`,
    );
  }
  return pairingBootstrap;
}

async function responseData(response: Response): Promise<Record<string, unknown>> {
  const payload = (await response.json()) as {
    data?: Record<string, unknown>;
    error?: { message?: string };
  };
  if (!response.ok || !payload.data) {
    throw new Error(payload.error?.message || `Pareamento local: HTTP ${response.status}`);
  }
  return payload.data;
}
