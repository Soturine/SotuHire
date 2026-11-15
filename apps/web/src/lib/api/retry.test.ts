import { describe, expect, it } from "vitest";

import { ApiHttpError } from "./client";
import { shouldRetryQuery } from "./retry";

describe("shouldRetryQuery", () => {
  it("never retries a definitive client answer such as 404 first use, 401 or 422", () => {
    for (const status of [400, 401, 403, 404, 409, 422]) {
      expect(shouldRetryQuery(0, new ApiHttpError(status, "x"))).toBe(false);
    }
  });

  it("retries timeouts, rate limits and server errors a bounded number of times", () => {
    expect(shouldRetryQuery(0, new ApiHttpError(429, "x"))).toBe(true);
    expect(shouldRetryQuery(2, new ApiHttpError(429, "x"))).toBe(false);
    expect(shouldRetryQuery(2, new ApiHttpError(503, "x"))).toBe(true);
    expect(shouldRetryQuery(3, new ApiHttpError(503, "x"))).toBe(false);
  });

  it("gives a refused connection a single retry", () => {
    expect(shouldRetryQuery(0, new TypeError("Failed to fetch"))).toBe(true);
    expect(shouldRetryQuery(1, new TypeError("Failed to fetch"))).toBe(false);
  });
});
