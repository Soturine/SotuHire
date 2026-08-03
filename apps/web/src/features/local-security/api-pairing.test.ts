import { afterEach, describe, expect, it, vi } from "vitest";

import { clearInMemoryPairing, pairedApiFetch } from "./api-pairing";

const BASE = "http://127.0.0.1:8787/api/v1";

afterEach(() => {
  clearInMemoryPairing();
  vi.restoreAllMocks();
});

describe("local API pairing", () => {
  it("exchanges a one-use proof, keeps credentials out of storage and retries with CSRF", async () => {
    const calls: Array<[string, RequestInit]> = [];
    const responses = [
      response(401, { error: { message: "pairing required" } }),
      response(200, { data: { challenge_id: "challenge-id-1234", proof: "proof-123456789012" } }),
      response(200, { data: { paired: true, csrf_token: "csrf-memory-only" } }),
      response(200, { data: { saved: true } }),
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init: RequestInit = {}) => {
        calls.push([url, init]);
        return responses.shift() as Response;
      }),
    );
    const storageSpy = vi.spyOn(Storage.prototype, "setItem");

    const result = await pairedApiFetch(BASE, "/profile/import-text", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: "fixture" }),
    });

    expect(result.status).toBe(200);
    expect(calls.map(([url]) => url)).toEqual([
      `${BASE}/profile/import-text`,
      "http://127.0.0.1:8787/api/v1/security/pairing/start",
      "http://127.0.0.1:8787/api/v1/security/pairing/complete",
      `${BASE}/profile/import-text`,
    ]);
    expect(calls[3][1].credentials).toBe("include");
    expect(calls[3][1].headers).toMatchObject({ "X-SotuHire-CSRF": "csrf-memory-only" });
    expect(storageSpy).not.toHaveBeenCalled();
  });
});

function response(status: number, payload: unknown): Response {
  return {
    status,
    ok: status >= 200 && status < 300,
    json: async () => payload,
  } as Response;
}
