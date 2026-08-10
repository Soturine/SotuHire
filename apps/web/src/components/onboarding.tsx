import { Link } from "@tanstack/react-router";
import { useState } from "react";

import { PreferenceFields } from "@/components/preferences-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { TranslationKey } from "@/lib/i18n";
import { usePreferences } from "@/lib/preferences";

const STEPS: Array<{
  title: TranslationKey;
  body: TranslationKey;
  to?: "/profile" | "/resume" | "/settings" | "/sources" | "/radar";
  page?: TranslationKey;
}> = [
  { title: "onboarding.step.preferences.title", body: "onboarding.step.preferences.body" },
  { title: "onboarding.step.localFirst.title", body: "onboarding.step.localFirst.body" },
  {
    title: "onboarding.step.profile.title",
    body: "onboarding.step.profile.body",
    to: "/profile",
    page: "route.profile.label",
  },
  {
    title: "onboarding.step.resume.title",
    body: "onboarding.step.resume.body",
    to: "/resume",
    page: "route.resume.label",
  },
  {
    title: "onboarding.step.ai.title",
    body: "onboarding.step.ai.body",
    to: "/settings",
    page: "route.settings.label",
  },
  {
    title: "onboarding.step.extension.title",
    body: "onboarding.step.extension.body",
    to: "/sources",
    page: "route.sources.label",
  },
  {
    title: "onboarding.step.opportunity.title",
    body: "onboarding.step.opportunity.body",
    to: "/radar",
    page: "route.radar.label",
  },
];

export function Onboarding() {
  const { onboardingComplete, completeOnboarding, t } = usePreferences();
  const [stepIndex, setStepIndex] = useState(0);
  const step = STEPS[stepIndex];
  const last = stepIndex === STEPS.length - 1;

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
        className="max-w-xl"
      >
        <DialogHeader>
          <p className="text-xs font-semibold uppercase tracking-wider text-accent">
            {t("onboarding.progress", { current: stepIndex + 1, total: STEPS.length })}
          </p>
          <DialogTitle>{t(step.title)}</DialogTitle>
          <DialogDescription>{t(step.body)}</DialogDescription>
        </DialogHeader>

        {stepIndex === 0 && <PreferenceFields />}
        {step.to && step.page && (
          <Link
            to={step.to}
            onClick={completeOnboarding}
            className="w-fit text-sm font-medium text-accent underline-offset-4 hover:underline"
          >
            {t("onboarding.openStep", { page: t(step.page) })}
          </Link>
        )}

        <div className="flex flex-wrap items-center justify-between gap-2 pt-2">
          <button
            type="button"
            onClick={completeOnboarding}
            className="rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted"
          >
            {t("onboarding.skip")}
          </button>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={stepIndex === 0}
              onClick={() => setStepIndex((value) => Math.max(0, value - 1))}
              className="rounded-md border border-input px-3 py-2 text-sm disabled:opacity-40"
            >
              {t("onboarding.back")}
            </button>
            <button
              type="button"
              onClick={() => (last ? completeOnboarding() : setStepIndex((value) => value + 1))}
              className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground"
            >
              {t(last ? "onboarding.finish" : "onboarding.next")}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
