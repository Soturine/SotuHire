import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { server } from "@/test/server";

import { makeApi } from "./client";

const baseUrl = "http://api.test/api/v1";

describe("data reliability client", () => {
  it("normalizes health issues from a real API envelope", async () => {
    server.use(
      http.get(`${baseUrl}/data/health`, () =>
        HttpResponse.json({
          ok: true,
          data: {
            checked_at: "2026-07-12T00:00:00Z",
            healthy: false,
            database_present: true,
            schema_version: 3,
            counts: { "sqlite:applications": 2 },
            issues: [
              {
                code: "application_job_snapshot_missing",
                severity: "warning",
                message: "Snapshot ausente",
                store: "applications",
                record_id: "application-1",
              },
            ],
          },
          warnings: [],
          request_id: "request-1",
        }),
      ),
    );

    const result = await makeApi("real", baseUrl).dataHealth();

    expect(result.healthy).toBe(false);
    expect(result.counts["sqlite:applications"]).toBe(2);
    expect(result.issues[0]).toMatchObject({
      severity: "warning",
      record_id: "application-1",
    });
  });

  it("preserves restore warnings provided by the envelope", async () => {
    server.use(
      http.post(`${baseUrl}/data/restore`, () =>
        HttpResponse.json({
          ok: true,
          data: {
            archive_name: "sotuhire-data-backup-test.zip",
            dry_run: true,
            files_validated: 4,
            files_restored: 0,
            pre_restore_backup_name: "",
            warnings: ["Aviso do arquivo"],
            message: "Backup validado.",
          },
          warnings: ["Aviso do envelope"],
        }),
      ),
    );

    const result = await makeApi("real", baseUrl).dataRestore({
      archive_name: "sotuhire-data-backup-test.zip",
    });

    expect(result.warnings).toEqual(["Aviso do arquivo", "Aviso do envelope"]);
    expect(result.dry_run).toBe(true);
  });

  it("surfaces the API error message", async () => {
    server.use(
      http.get(`${baseUrl}/data/backups`, () =>
        HttpResponse.json(
          {
            ok: false,
            error: { code: "archive_error", message: "Backup inválido" },
          },
          { status: 400 },
        ),
      ),
    );

    await expect(makeApi("real", baseUrl).dataArchives()).rejects.toThrow("Backup inválido");
  });
});
