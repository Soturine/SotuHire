import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { afterEach, describe, expect, it, vi } from "vitest";

import { clearInMemoryPairing } from "@/features/local-security/api-pairing";
import { makeApi } from "./client";

/**
 * Client ↔ API request contract (follow-up of SH-NEW-032). Every Local API request model forbids
 * unknown fields, so a field the client adds is a 422 in API mode that sample mode never shows: the
 * Tracker sent `source` for months. Here the payloads are the ones the screens build, from the
 * client's own sample data (an import draft item, a Profile fact, a stored variant…); each write is
 * sent through the real-mode client with fetch captured, and the body is checked against the
 * committed OpenAPI document (refresh: python scripts/export_openapi.py; pytest checks drift).
 */

type Schema = {
  $ref?: string;
  type?: string;
  properties?: Record<string, Schema>;
  required?: string[];
  additionalProperties?: boolean | Schema;
  items?: Schema;
  anyOf?: Schema[];
  allOf?: Schema[];
};
type Spec = {
  paths: Record<
    string,
    Record<string, { requestBody?: { content: Record<string, { schema: Schema }> } }>
  >;
  components: { schemas: Record<string, Schema> };
};

const spec = JSON.parse(
  readFileSync(resolve(__dirname, "../../../tests/contract/openapi.json"), "utf-8"),
) as Spec;
const BASE = "http://127.0.0.1:8787/api/v1";

function deref(schema: Schema): Schema {
  let current = schema;
  while (current.$ref) current = spec.components.schemas[current.$ref.split("/").pop()!]!;
  if (current.allOf?.length === 1) return deref(current.allOf[0]!);
  return current;
}

/** Problems of `value` against `schema`: unknown fields where the model forbids them, missing required ones. */
function violations(value: unknown, schema: Schema, at: string): string[] {
  const resolved = deref(schema);
  if (value === null || value === undefined) return [];
  if (resolved.anyOf) {
    const options = resolved.anyOf.map((option) => violations(value, option, at));
    return options.some((problems) => problems.length === 0) ? [] : options[0]!;
  }
  if (Array.isArray(value)) {
    return resolved.items
      ? value.flatMap((item, index) => violations(item, resolved.items!, `${at}[${index}]`))
      : [];
  }
  if (typeof value !== "object" || !resolved.properties) return [];
  const problems: string[] = [];
  const record = value as Record<string, unknown>;
  for (const key of Object.keys(record)) {
    const property = resolved.properties[key];
    if (!property) {
      if (resolved.additionalProperties === false)
        problems.push(`${at}.${key} is not in the contract`);
      continue;
    }
    problems.push(...violations(record[key], property, `${at}.${key}`));
  }
  for (const key of resolved.required ?? []) {
    if (!(key in record)) problems.push(`${at}.${key} is required`);
  }
  return problems;
}

function requestSchema(method: string, url: string): Schema | undefined {
  const path = new URL(url).pathname;
  for (const [template, operations] of Object.entries(spec.paths)) {
    const pattern = new RegExp(`^${template.replace(/\{[^}]+\}/g, "[^/]+")}$`);
    if (!pattern.test(path)) continue;
    return operations[method.toLowerCase()]?.requestBody?.content["application/json"]?.schema;
  }
  return undefined;
}

type Captured = { method: string; url: string; body: unknown };

function captureFetch(): Captured[] {
  const captured: Captured[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init: RequestInit = {}) => {
      captured.push({
        method: init.method ?? "GET",
        url,
        body: typeof init.body === "string" ? JSON.parse(init.body) : undefined,
      });
      return new Response(JSON.stringify({ ok: true, data: {}, warnings: [], request_id: "t" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }),
  );
  return captured;
}

afterEach(() => {
  clearInMemoryPairing();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("client request bodies match the API contract", () => {
  it("sends only contract fields for the writes the screens make with domain objects", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout"] });
    const demo = makeApi("demo", BASE);
    const settle = async <T>(promise: Promise<T>) => {
      await vi.runAllTimersAsync();
      return promise;
    };
    const draft = await settle(
      demo.profileImportText({ text: "Estágio em obra", source_type: "resume", use_ai: false }),
    );
    const lattes = await settle(
      demo.profileImportLattes({
        text: "Mestrado",
        source_url: "",
        lattes_id: "",
        orcid: "",
        use_ai: false,
      }),
    );
    const profile = (await settle(demo.profile())).profile;
    const jobs = (await settle(demo.trackerJobs())).jobs;
    const variant = (await settle(demo.resumeStudioVariants("m"))).items[0]!;
    const master = (await settle(demo.resumeStudioMaster())).resume;
    vi.useRealTimers();

    const captured = captureFetch();
    const real = makeApi("real", BASE);
    const item = profile.items[0]!;
    const writes: Array<[string, () => Promise<unknown>]> = [
      ["profileAddItem(import draft item)", () => real.profileAddItem(draft.items[0]!)],
      [
        "profileAddItem(add-fact dialog)",
        () =>
          real.profileAddItem({
            type: "project",
            title: "NR10",
            organization: "",
            domain: "",
            evidence: "Certificado",
            area: "",
            description: "Certificado",
            source: "manual",
          }),
      ],
      ["profilePatchItem(confirm)", () => real.profilePatchItem(item.item_id, {})],
      [
        "profilePatchItem(edit)",
        () =>
          real.profilePatchItem(item.item_id, {
            title: "t",
            organization: "o",
            domain: "d",
            area: "d",
            evidence: "e",
            description: "e",
          }),
      ],
      ["profileConfirmLattes(draft items)", () => real.profileConfirmLattes(lattes.items)],
      [
        "trackerCreate",
        () =>
          real.trackerCreate({
            title: "Enfermeira",
            company: "H",
            source: "Gupy",
            status: "found",
          }),
      ],
      ["trackerUpdate(status)", () => real.trackerUpdate(jobs[0]!.id, { status: "applied" })],
      ["resumeStudioSaveVariant(stored variant)", () => real.resumeStudioSaveVariant(variant)],
      [
        "resumeStudioUpdateVariant(autosave)",
        () =>
          real.resumeStudioUpdateVariant(
            variant.resume_variant_id,
            {
              title: variant.title,
              target_role: variant.target_role,
              sections: variant.sections,
              validation_warnings: variant.validation_warnings,
            },
            variant.updated_at,
          ),
      ],
      ["resumeStudioSaveMaster(master)", () => real.resumeStudioSaveMaster(master)],
    ];

    const problems: string[] = [];
    for (const [name, write] of writes) {
      const before = captured.length;
      await write().catch(() => undefined); // the stub answers {}: response parsing may fail
      const sent = captured.slice(before).filter((call) => call.method !== "GET");
      if (!sent.length) {
        problems.push(`${name}: no request was sent`);
        continue;
      }
      for (const call of sent) {
        const schema = requestSchema(call.method, call.url);
        if (!schema) {
          problems.push(
            `${name}: ${call.method} ${new URL(call.url).pathname} has no request schema`,
          );
          continue;
        }
        problems.push(...violations(call.body, schema, name));
      }
    }
    expect(problems).toEqual([]);
  }, 30_000);

  it("would catch the Tracker regression (negative control)", () => {
    const schema = requestSchema("POST", `${BASE}/tracker/jobs`)!;
    expect(violations({ title: "x", source: "Gupy" }, schema, "body")).toEqual([
      "body.source is not in the contract",
    ]);
  });
});
