import { QueryClient, QueryObserver } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";

import type { TrackerJob, TrackerJobsResult } from "@/lib/api/types";

import { addCreatedJob } from "./jobs-cache";

const job = (id: string, title: string): TrackerJob => ({
  id,
  title,
  company: "Empresa Fictícia",
  status: "found",
});

const list = (...jobs: TrackerJob[]): TrackerJobsResult => ({
  jobs,
  context_summary: "",
  job_contexts: {},
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => (resolve = r));
  return { promise, resolve };
}

describe("addCreatedJob (SH-NEW-041)", () => {
  it("keeps an application created while the list request is still in flight", async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const key = ["tracker-jobs", "test"];
    const seed = job("seed", "Vaga de exemplo");
    const created = job("new", "Backend Python");
    const stale = deferred<TrackerJobsResult>();
    // The server: the first request was asked before the creation, every later one after it.
    let requests = 0;
    const queryFn = () => {
      requests += 1;
      return requests === 1 ? stale.promise : Promise.resolve(list(created, seed));
    };
    const observer = new QueryObserver<TrackerJobsResult>(qc, { queryKey: key, queryFn });
    const unsubscribe = observer.subscribe(() => undefined); // the board is mounted

    await addCreatedJob(qc, key, created); // the creation answers first
    stale.resolve(list(seed)); // then the older list request answers
    await new Promise((r) => setTimeout(r, 0));
    await qc.getQueryCache().find({ queryKey: key })?.promise;

    const ids = qc.getQueryData<TrackerJobsResult>(key)?.jobs.map((item) => item.id);
    unsubscribe();
    expect(ids).toEqual(["new", "seed"]);
  });

  it("shows the application before the list is asked again", async () => {
    const qc = new QueryClient();
    const key = ["tracker-jobs", "test"];
    qc.setQueryData(key, list(job("seed", "Vaga de exemplo")));
    void addCreatedJob(qc, key, job("new", "Backend Python"));
    expect(qc.getQueryData<TrackerJobsResult>(key)?.jobs.map((item) => item.id)).toEqual([
      "new",
      "seed",
    ]);
  });
});
