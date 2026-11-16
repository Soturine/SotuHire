"""Adversarial UI mutants (CP-UX06, addendum v5 §12).

Each mutant breaks one promise the interface makes (a human-approval interlock, an accessible
name, a "no false zeros" state, a conflict guard) with a one-line edit, runs the E2E spec that is
supposed to protect it, records whether the suite failed (killed) or passed (survived), and restores
the file byte for byte. A survivor is a gap in the tests, not in the product.

    python scripts/ui-mutants.py [--only ID] [--out report.json]

Run from apps/web with nothing else editing src/ (the Vite dev server reloads the mutated file).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]

MUTANTS = [
    {
        "id": "approve-all",
        "promise": "there is no Approve all",
        "file": "src/routes/approvals.tsx",
        "old": '<div role="group" aria-label={t.title} className="flex flex-wrap gap-1.5">',
        "new": '<div role="group" aria-label={t.title} className="flex flex-wrap gap-1.5"><button type="button">Aprovar tudo</button>',
        "spec": "tests/e2e/control-ux.spec.ts",
        "grep": "approve → run → undo",
    },
    {
        "id": "silent-transition-failure",
        "promise": "a refused transition is said",
        "file": "src/routes/approvals.tsx",
        "old": "onError: (error: Error) => toast.error(`${t.failed}: ${error.message}`),",
        "new": "onError: () => undefined,",
        "spec": "tests/e2e/control-ux.spec.ts",
        "grep": "refused transition",
    },
    {
        "id": "accept-claim-without-evidence",
        "promise": "a change without evidence cannot be accepted in the Lab",
        "file": "src/routes/application-lab.tsx",
        "old": "disabled={pending || (!item.evidence_used.length && Boolean(item.after))}",
        "new": "disabled={pending}",
        "spec": "tests/e2e/control-ux.spec.ts",
        "grep": "lab tells advice apart",
    },
    {
        "id": "autosave-ignores-conflict",
        "promise": "a variant saved elsewhere is never overwritten silently",
        "file": "src/routes/resume-studio.tsx",
        "old": "mutationFn: (variant: ResumeVariant) => persist(variant, serverVersion.current),",
        "new": "mutationFn: (variant: ResumeVariant) => persist(variant, null),",
        "spec": "tests/e2e/resume-studio-profile.spec.ts",
        "grep": "saved elsewhere",
    },
    {
        "id": "remove-without-confirm",
        "promise": "removing a Profile fact asks first",
        "file": "src/routes/profile.tsx",
        "old": "<AlertDialogTrigger asChild>",
        "new": "<AlertDialogTrigger asChild onClickCapture={onDelete}>",
        "spec": "tests/e2e/profile-resume-ux.spec.ts",
        "grep": "removing a fact asks first",
    },
    {
        "id": "zeros-when-api-down",
        "promise": "the Cockpit never shows zeros as data when the API is down",
        "file": "src/routes/dashboard.tsx",
        "old": "{state.isError ? (",
        "new": "{false ? (",
        "spec": "tests/e2e/journey-shell.spec.ts",
        "grep": "API down",
    },
    {
        "id": "tracker-select-unnamed",
        "promise": "each Tracker status control is named",
        "file": "src/routes/tracker.tsx",
        "old": "aria-label={`Status de ${j.title}`}",
        "new": "",
        "spec": "tests/e2e/opportunities-ux.spec.ts",
        "grep": "on a phone",
    },
    {
        "id": "tracker-filter-accent-sensitive",
        "promise": "the Tracker filter ignores accents",
        "file": "src/routes/tracker.tsx",
        "old": 'const haystack = normalize(`${j.title} ${j.company} ${j.source ?? ""}`);',
        "new": 'const haystack = `${j.title} ${j.company} ${j.source ?? ""}`.toLowerCase();',
        "spec": "tests/e2e/opportunities-ux.spec.ts",
        "grep": "tracker filter",
    },
    {
        "id": "settings-revert-unsaved-choice",
        "promise": "a refetch does not revert an unsaved AI provider choice",
        "file": "src/routes/settings.tsx",
        "old": "if (snapshot === hydratedFrom.current) return;",
        "new": "",
        "spec": "tests/e2e/smoke.spec.ts",
        "grep": "Claude can be chosen",
    },
    {
        "id": "profile-drift-applied-silently",
        "promise": "Profile edits reach the Master only on request",
        "file": "src/features/resume-studio/profile-sync.tsx",
        "old": "disabled={!refreshSelected.size || refresh.isPending}",
        "new": "disabled={refresh.isPending}",
        "spec": "tests/e2e/profile-resume-ux.spec.ts",
        "grep": "only after it is chosen",
    },
]


def run(mutant: dict) -> dict:
    path = ROOT / mutant["file"]
    original = path.read_bytes()
    text = original.decode("utf-8")
    if mutant["old"] not in text:
        return {**_meta(mutant), "status": "NOT_APPLIED", "reason": "anchor not found"}
    path.write_bytes(text.replace(mutant["old"], mutant["new"], 1).encode("utf-8"))
    try:
        time.sleep(1.5)  # let the dev server see the change
        started = time.time()
        proc = subprocess.run(
            [
                "npx",
                "playwright",
                "test",
                mutant["spec"],
                "--project=chromium",
                "--workers=1",
                "--retries=0",
                "--reporter=line",
                "--grep",
                mutant["grep"],
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True,
            timeout=600,
        )
        tail = [line for line in proc.stdout.splitlines() if line.strip()][-3:]
        return {
            **_meta(mutant),
            "status": "KILLED" if proc.returncode != 0 else "SURVIVED",
            "exit_code": proc.returncode,
            "seconds": round(time.time() - started, 1),
            "summary": tail,
        }
    finally:
        path.write_bytes(original)
        time.sleep(1.0)


def _meta(mutant: dict) -> dict:
    return {key: mutant[key] for key in ("id", "promise", "file", "spec", "grep")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    chosen = [m for m in MUTANTS if not args.only or m["id"] in args.only]
    results = [run(m) for m in chosen]
    report = {
        "kind": "sotuhire-ui-mutants",
        "browser": "chromium",
        "results": results,
        "killed": sum(r["status"] == "KILLED" for r in results),
        "survived": sum(r["status"] == "SURVIVED" for r in results),
        "not_applied": sum(r["status"] == "NOT_APPLIED" for r in results),
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        pathlib.Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
