const assert = require("assert");
const path = require("path");

require(path.resolve(process.argv[2], "queue_runtime.js"));

const queue = globalThis.SotuHireQueue;

(async () => {
  const firstDate = new Date("2026-01-01T00:00:00.000Z");
  const secondDate = new Date("2026-01-01T00:01:00.000Z");
  let pending = queue.upsert(
    [],
    {
      path: "/capture/job",
      body: {
        capture_id: "capture-one",
        url: "https://jobs.example/vaga/42?utm_source=mail&ref=home&a=1",
      },
      label: "Vaga",
    },
    firstDate,
  );
  pending = queue.upsert(
    pending,
    {
      path: "/capture/job",
      body: {
        capture_id: "capture-two",
        url: "https://jobs.example/vaga/42?a=1&utm_campaign=social#details",
        api_key: "must-not-be-stored",
      },
      label: "Vaga atualizada",
    },
    secondDate,
  );

  assert.strictEqual(pending.length, 1);
  assert.strictEqual(pending[0].body.capture_id, "capture-two");
  assert(!Object.hasOwn(pending[0].body, "api_key"));
  assert.strictEqual(pending[0].queued_at, firstDate.toISOString());
  assert.strictEqual(
    pending[0].identity,
    "/capture/job|https://jobs.example/vaga/42?a=1",
  );

  let calls = 0;
  const fail = async () => {
    calls += 1;
    throw new Error("Companion offline");
  };
  const start = Date.parse("2026-01-01T01:00:00.000Z");
  let retried = await queue.retry(pending, fail, { force: true, now: start });
  assert.strictEqual(retried.remaining[0].retry_count, 1);
  assert.strictEqual(
    Date.parse(retried.remaining[0].next_retry_at) - start,
    queue.BACKOFF_MS,
  );

  const skipped = await queue.retry(retried.remaining, fail, {
    force: false,
    now: start + queue.BACKOFF_MS - 1,
  });
  assert.strictEqual(calls, 1);
  assert.strictEqual(skipped.remaining[0].retry_count, 1);

  let current = skipped.remaining;
  for (let attempt = 2; attempt <= queue.MAX_ATTEMPTS; attempt += 1) {
    retried = await queue.retry(current, fail, {
      force: true,
      now: start + attempt * 100000,
    });
    current = retried.remaining;
    assert.strictEqual(current[0].retry_count, attempt);
  }
  assert.strictEqual(current[0].state, "failed");
  const callsAtLimit = calls;
  await queue.retry(current, fail, { force: true, now: start + 9999999 });
  assert.strictEqual(calls, callsAtLimit);

  const geminiLike = "AIza" + "A".repeat(28);
  const openAiLike = "sk-" + "B".repeat(28);
  const exported = queue.exportPayload([
    {
      identity: "unsafe",
      path: "/capture/job",
      body: {
        url: "https://jobs.example/vaga/99",
        apiKey: "field-secret",
        nested: { Authorization: "Bearer field-secret", token: "field-secret" },
        visible_text: `Valores acidentais ${geminiLike} e ${openAiLike}`,
      },
    },
  ]);
  const serialized = JSON.stringify(exported);
  assert(!serialized.includes(geminiLike));
  assert(!serialized.includes(openAiLike));
  assert(!Object.hasOwn(exported.items[0].body, "apiKey"));
  assert.deepStrictEqual(exported.items[0].body.nested, {});

  const imported = queue.importPayload({
    format: "sotuhire-extension-queue",
    version: 1,
    items: [
      {
        identity: "forged-one",
        path: "/capture/job",
        body: {
          url: "https://jobs.example/vaga/7?utm_source=a",
          api_key: "remove-me",
        },
      },
      {
        identity: "forged-two",
        path: "/capture/job",
        body: { url: "https://jobs.example/vaga/7?ref=other" },
      },
      {
        identity: "unsafe-path",
        path: "/admin/delete",
        body: { url: "https://jobs.example/vaga/8" },
      },
    ],
  });
  assert.strictEqual(imported.length, 1);
  assert.strictEqual(
    imported[0].identity,
    "/capture/job|https://jobs.example/vaga/7",
  );
  assert(!Object.hasOwn(imported[0].body, "api_key"));

  process.stdout.write(
    JSON.stringify({
      deduplicated: pending.length,
      retryCount: current[0].retry_count,
      state: current[0].state,
      safeExport: true,
      safeImport: true,
    }),
  );
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
