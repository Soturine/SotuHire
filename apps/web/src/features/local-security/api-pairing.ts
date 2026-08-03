const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

let csrfToken = "";
let pairingPromise: Promise<void> | null = null;

export async function pairedApiFetch(
  baseUrl: string,
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const first = await fetchWithSession(baseUrl, path, init);
  if (first.status !== 401) return first;
  await pairLocalApi(baseUrl);
  return fetchWithSession(baseUrl, path, init);
}

export function pairLocalApi(baseUrl: string): Promise<void> {
  pairingPromise ??= exchangePairing(baseUrl).finally(() => {
    pairingPromise = null;
  });
  return pairingPromise;
}

export function clearInMemoryPairing(): void {
  csrfToken = "";
}

async function exchangePairing(baseUrl: string): Promise<void> {
  const apiRoot = baseUrl.replace(/\/api\/v1\/?$/, "");
  const start = await fetch(`${apiRoot}/api/v1/security/pairing/start`, {
    method: "POST",
    credentials: "include",
    headers: { "content-type": "application/json" },
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
  csrfToken = String(paired.csrf_token || "");
  if (!csrfToken) throw new Error("O pareamento local não retornou proteção CSRF.");
}

async function fetchWithSession(
  baseUrl: string,
  path: string,
  init: RequestInit,
): Promise<Response> {
  const method = String(init.method || "GET").toUpperCase();
  return fetch(`${baseUrl.replace(/\/+$/, "")}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(MUTATING_METHODS.has(method) && csrfToken ? { "X-SotuHire-CSRF": csrfToken } : {}),
      ...(init.headers ?? {}),
    },
  });
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
