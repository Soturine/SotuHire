import { ApiHttpError } from "./client";

/**
 * Query retry policy. A 4xx is the API's answer, not a hiccup: "no Master Resume yet" (404) must
 * show the first-use screen at once, not after ~7 s of retries with a spinner. Timeouts and rate
 * limits (408, 429) and server errors are retried; a refused connection only once, since a local
 * API that is down will not come back in the next seconds.
 */
export function shouldRetryQuery(failures: number, error: unknown): boolean {
  if (error instanceof ApiHttpError) {
    if (error.status === 408 || error.status === 429) return failures < 2;
    if (error.status >= 400 && error.status < 500) return false;
    return failures < 3;
  }
  if (/Failed to fetch|NetworkError|Load failed/i.test(String(error))) return failures < 1;
  return failures < 3;
}
