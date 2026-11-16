import type { ResumeVariant } from "@/lib/api/types";

/* Browser drafts of the Resume Studio. The server copy is the saved state; a draft only bridges
   an interrupted save (offline, API down) and never silently replaces newer server content. */

export function draftKey(masterResumeId: string): string {
  return `sotuhire:resume-draft:${masterResumeId}`;
}

export function safeStorage(action: () => void): void {
  try {
    action();
  } catch {
    /* storage can be unavailable (private mode, quota); the server copy still holds. */
  }
}

export function readDraft(storageKey: string): ResumeVariant | null {
  try {
    const stored = localStorage.getItem(storageKey);
    return stored ? (JSON.parse(stored) as ResumeVariant) : null;
  } catch {
    return null;
  }
}

/** A browser draft wins only when it is the same variant and newer than what the server holds. */
export function pickDraft(
  draft: ResumeVariant | null,
  server: ResumeVariant,
): { variant: ResumeVariant; restoredDraft: boolean } {
  if (!draft || draft.resume_variant_id !== server.resume_variant_id) {
    return { variant: server, restoredDraft: false };
  }
  const draftTime = Date.parse(draft.updated_at);
  const serverTime = Date.parse(server.updated_at);
  return Number.isFinite(draftTime) && (!Number.isFinite(serverTime) || draftTime > serverTime)
    ? { variant: draft, restoredDraft: true }
    : { variant: server, restoredDraft: false };
}
