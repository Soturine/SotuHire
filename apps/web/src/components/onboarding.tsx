import { Link } from "@tanstack/react-router";
import {
  ArrowRight,
  FileText,
  HardDrive,
  Radar,
  ShieldCheck,
  Sparkles,
  UserRound,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";

import { BrandMark } from "@/components/brand";
import { PreferenceFields } from "@/components/preferences-dialog";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { TranslationKey } from "@/lib/i18n";
import { usePreferences } from "@/lib/preferences";

/**
 * First visit, CP-UX02: two steps instead of eight modal pages. The first sets language and theme
 * and states the three rules of the product; the second offers the starting paths as links. The
 * texts of the former steps are kept, only regrouped.
 */
const PRINCIPLES: Array<{ icon: LucideIcon; title: TranslationKey; body: TranslationKey }> = [
  {
    icon: HardDrive,
    title: "onboarding.step.localFirst.title",
    body: "onboarding.step.localFirst.body",
  },
  { icon: Sparkles, title: "onboarding.step.ai.title", body: "onboarding.step.ai.body" },
  {
    icon: ShieldCheck,
    title: "onboarding.step.approval.title",
    body: "onboarding.step.approval.body",
  },
];

const PATHS: Array<{
  icon: LucideIcon;
  to: "/profile" | "/resume-studio" | "/radar" | "/sources";
  title: TranslationKey;
  body: TranslationKey;
}> = [
  {
    icon: UserRound,
    to: "/profile",
    title: "onboarding.step.profile.title",
    body: "onboarding.step.profile.body",
  },
  {
    icon: FileText,
    to: "/resume-studio",
    title: "onboarding.step.resume.title",
    body: "onboarding.step.resume.body",
  },
  {
    icon: Radar,
    to: "/radar",
    title: "onboarding.step.opportunity.title",
    body: "onboarding.step.opportunity.body",
  },
  {
    icon: ArrowRight,
    to: "/sources",
    title: "onboarding.step.extension.title",
    body: "onboarding.step.extension.body",
  },
];

export function Onboarding() {
  const { onboardingComplete, completeOnboarding, t } = usePreferences();
  const [stepIndex, setStepIndex] = useState(0);
  const total = 2;

  return (
    <Dialog
      open={!onboardingComplete}
      onOpenChange={(open) => {
        if (!open) completeOnboarding();
      }}
    >
      <DialogContent
        aria-label={t("onboarding.regionLabel")}
        onEscapeKeyDown={completeOnboarding}
        className="max-h-[92vh] max-w-2xl overflow-y-auto"
      >
        <DialogHeader>
          <div className="flex items-center gap-3">
            <BrandMark className="h-9 w-9" />
            <p className="eyebrow text-accent-strong">
              {t("onboarding.progress", { current: stepIndex + 1, total })}
            </p>
          </div>
          <DialogTitle className="text-display pt-2 text-2xl">
            {t(stepIndex === 0 ? "onboarding.step.preferences.title" : "onboarding.start.title")}
          </DialogTitle>
          <DialogDescription>
            {t(stepIndex === 0 ? "onboarding.step.preferences.body" : "onboarding.start.body")}
          </DialogDescription>
        </DialogHeader>

        {stepIndex === 0 ? (
          <div key="preferences" className="animate-page-in space-y-5">
            <PreferenceFields />
            <section aria-labelledby="onboarding-principles">
              <h3 id="onboarding-principles" className="eyebrow text-muted-foreground">
                {t("onboarding.principles")}
              </h3>
              <ul className="mt-2 grid gap-2 sm:grid-cols-3">
                {PRINCIPLES.map(({ icon: Icon, title, body }) => (
                  <li key={title} className="rounded-xl border bg-surface p-3">
                    <Icon aria-hidden className="h-4 w-4 text-accent-strong" />
                    <p className="mt-2 text-sm font-semibold">{t(title)}</p>
                    <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{t(body)}</p>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        ) : (
          <ul key="paths" className="animate-page-in grid gap-2 sm:grid-cols-2">
            {PATHS.map(({ icon: Icon, to, title, body }) => (
              <li key={to}>
                <Link
                  to={to}
                  onClick={completeOnboarding}
                  className="group flex h-full gap-3 rounded-xl border bg-card p-4 shadow-[var(--shadow-soft)] transition-[border-color,box-shadow,transform] duration-(--duration-2) ease-(--ease-out) hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-[var(--shadow-elevated)]"
                >
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-surface-accent text-accent-strong">
                    <Icon aria-hidden className="h-4 w-4" />
                  </span>
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold">{t(title)}</span>
                    <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">
                      {t(body)}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}

        <div className="flex flex-wrap items-center justify-between gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={completeOnboarding}>
            {t("onboarding.skip")}
          </Button>
          <div className="flex gap-2">
            {stepIndex === 1 && (
              <Button type="button" variant="outline" onClick={() => setStepIndex(0)}>
                {t("onboarding.back")}
              </Button>
            )}
            <Button
              type="button"
              onClick={() => (stepIndex === 0 ? setStepIndex(1) : completeOnboarding())}
            >
              {t(stepIndex === 0 ? "onboarding.next" : "onboarding.start.explore")}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
