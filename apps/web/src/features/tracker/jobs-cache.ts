import type { QueryClient, QueryKey } from "@tanstack/react-query";

import type { TrackerJob, TrackerJobsResult } from "@/lib/api/types";

/** Show a just-created application at once, then reconcile the list with the source of truth.
 *
 * SH-NEW-041: a list request already in flight when the application was saved answered with the
 * list as it was before, and that answer replaced the cache: the new application vanished. The
 * invalidation cancels that request (``cancelRefetch``) and asks again, so the answer that lands
 * last already contains it. */
export function addCreatedJob(qc: QueryClient, key: QueryKey, job: TrackerJob): Promise<void> {
  qc.setQueryData<TrackerJobsResult>(key, (current) => ({
    context_summary: current?.context_summary ?? "",
    job_contexts: current?.job_contexts ?? {},
    jobs: [job, ...(current?.jobs ?? []).filter((item) => item.id !== job.id)],
  }));
  return qc.invalidateQueries({ queryKey: key }, { cancelRefetch: true });
}
