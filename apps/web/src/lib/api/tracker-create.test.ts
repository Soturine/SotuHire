import { describe, expect, it } from "vitest";

import { trackerCreateBody } from "./client";

// Fields of TrackerJobCreateRequest (apps/api/schemas/analysis.py, extra="forbid").
const CONTRACT = new Set([
  "title",
  "company",
  "source_url",
  "modality",
  "seniority",
  "requirements",
  "status",
  "match_score",
  "ats_score",
  "opportunity_fit_score",
  "risk_score",
  "recommendation",
  "collection_method",
  "notes",
  "job_text",
  "resume_text",
  "profile_id",
  "resume_variant_id",
  "source_capture_id",
  "privacy_acknowledged",
  "request_id",
]);

describe("trackerCreateBody", () => {
  it("sends only fields the API accepts and maps source to source_url", () => {
    const body = trackerCreateBody({
      id: "local-only",
      title: "Enfermeira",
      company: "Hospital",
      source: "Gupy",
      status: "found",
      notes: "nota",
      updated_at: "2026-11-15",
    });
    expect(Object.keys(body).filter((key) => !CONTRACT.has(key))).toEqual([]);
    expect(body.source_url).toBe("Gupy");
    expect(body).not.toHaveProperty("source");
  });
});
