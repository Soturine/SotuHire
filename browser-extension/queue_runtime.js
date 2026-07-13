(() => {
  const MAX_ATTEMPTS = 5;
  const BACKOFF_MS = 30000;
  const TRACKING_PARAMETERS = new Set([
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_",
    "tracking",
    "tracking_id",
    "trackingid",
  ]);
  const SECRET_FIELD =
    /(api.?key|authorization|access.?token|refresh.?token|token|cookie|secret|password|passphrase|private.?key|credential)/i;
  const SECRET_VALUE_PATTERNS = [
    /AIza[0-9A-Za-z_-]{20,}/g,
    /AQ\.[0-9A-Za-z_-]{20,}/g,
    /sk-(?:proj-)?[0-9A-Za-z_-]{20,}/g,
  ];

  const normalizeUrl = (value) => {
    try {
      const parsed = new URL(value);
      for (const key of [...parsed.searchParams.keys()]) {
        const normalizedKey = key.toLowerCase();
        if (
          normalizedKey.startsWith("utm_") ||
          TRACKING_PARAMETERS.has(normalizedKey)
        ) {
          parsed.searchParams.delete(key);
        }
      }
      parsed.searchParams.sort();
      parsed.hash = "";
      return parsed.toString().replace(/\/$/, "");
    } catch (_error) {
      return String(value || "");
    }
  };

  const stableHash = (value) => {
    const input = JSON.stringify(value);
    let hash = 2166136261;
    for (let index = 0; index < input.length; index += 1) {
      hash ^= input.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return (hash >>> 0).toString(16).padStart(8, "0");
  };

  const identityFor = (path, body) => {
    const reference =
      body?.url || body?.capture?.url || body?.source_url || body?.capture_id || "";
    const identity = reference
      ? normalizeUrl(reference)
      : `payload:${stableHash(body || {})}`;
    return `${path}|${identity}`;
  };

  const upsert = (pending, { path, body, label }, now = new Date()) => {
    const safeBody = sanitize(body);
    const identity = identityFor(path, safeBody);
    const previous = pending.find(
      (item) => identityFor(item.path, item.body) === identity,
    );
    const result = pending.filter(
      (item) => identityFor(item.path, item.body) !== identity,
    );
    result.push({
      identity,
      path,
      body: safeBody,
      label: sanitize(label),
      queued_at: previous?.queued_at || previous?.queuedAt || now.toISOString(),
      retry_count: 0,
      last_error: "",
      next_retry_at: now.toISOString(),
      state: "pending",
      max_attempts: MAX_ATTEMPTS,
    });
    return result;
  };

  const retry = async (pending, sender, { force = true, now = Date.now() } = {}) => {
    const remaining = [];
    let sent = 0;
    for (const item of pending) {
      const rawAttempts = Number(item.retry_count);
      const attempts = Number.isFinite(rawAttempts)
        ? Math.max(0, Math.trunc(rawAttempts))
        : 0;
      const rawMaxAttempts = Number(item.max_attempts);
      const maxAttempts = Number.isFinite(rawMaxAttempts)
        ? Math.min(MAX_ATTEMPTS, Math.max(1, Math.trunc(rawMaxAttempts)))
        : MAX_ATTEMPTS;
      if (attempts >= maxAttempts) {
        remaining.push({ ...item, state: "failed" });
        continue;
      }
      if (!force && item.next_retry_at && new Date(item.next_retry_at).getTime() > now) {
        remaining.push(item);
        continue;
      }
      try {
        await sender(item.path, item.body);
        sent += 1;
      } catch (error) {
        const retryCount = attempts + 1;
        remaining.push({
          ...item,
          retry_count: retryCount,
          last_error: sanitize(
            String(error?.message || "Falha de conexão").slice(0, 300),
          ),
          next_retry_at: new Date(
            now + BACKOFF_MS * 2 ** Math.max(0, retryCount - 1),
          ).toISOString(),
          state: retryCount >= maxAttempts ? "failed" : "pending",
          max_attempts: maxAttempts,
        });
      }
    }
    return { remaining, sent };
  };

  const sanitize = (value) => {
    if (Array.isArray(value)) return value.map(sanitize);
    if (typeof value === "string") {
      return SECRET_VALUE_PATTERNS.reduce(
        (result, pattern) => result.replace(pattern, "[secret]"),
        value,
      );
    }
    if (!value || typeof value !== "object") return value;
    return Object.fromEntries(
      Object.entries(value)
        .filter(([key]) => !SECRET_FIELD.test(key))
        .map(([key, item]) => [key, sanitize(item)]),
    );
  };

  const exportPayload = (items, now = new Date()) => ({
    format: "sotuhire-extension-queue",
    version: 1,
    exported_at: now.toISOString(),
    items: items.map(sanitize),
  });

  const importPayload = (payload, current = []) => {
    if (payload?.format !== "sotuhire-extension-queue" || !Array.isArray(payload.items)) {
      throw new Error("Arquivo de fila incompatível.");
    }
    const byIdentity = new Map();
    for (const item of current) {
      if (typeof item?.path !== "string" || !item?.body) continue;
      const safe = sanitize(item);
      const identity = identityFor(safe.path, safe.body);
      byIdentity.set(identity, { ...safe, identity });
    }
    for (const item of payload.items.slice(0, 500)) {
      if (typeof item?.path !== "string" || !item.path.startsWith("/capture/")) {
        continue;
      }
      if (!item?.body || typeof item.body !== "object" || Array.isArray(item.body)) {
        continue;
      }
      const safe = sanitize(item);
      const identity = identityFor(safe.path, safe.body);
      const rawRetryCount = Number(safe.retry_count);
      const retryCount = Math.trunc(Math.min(
        MAX_ATTEMPTS,
        Math.max(0, Number.isFinite(rawRetryCount) ? rawRetryCount : 0),
      ));
      const nextRetry = Date.parse(safe.next_retry_at);
      byIdentity.set(identity, {
        ...safe,
        identity,
        retry_count: retryCount,
        max_attempts: MAX_ATTEMPTS,
        next_retry_at: Number.isFinite(nextRetry)
          ? new Date(nextRetry).toISOString()
          : new Date().toISOString(),
        state: retryCount >= MAX_ATTEMPTS ? "failed" : "pending",
      });
    }
    return [...byIdentity.values()];
  };

  globalThis.SotuHireQueue = {
    MAX_ATTEMPTS,
    BACKOFF_MS,
    normalizeUrl,
    identityFor,
    upsert,
    retry,
    sanitize,
    exportPayload,
    importPayload,
  };
})();
