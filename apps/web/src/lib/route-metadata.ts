import type { TranslationKey } from "@/lib/i18n";

export interface RouteMetadata {
  path: string;
  label: TranslationKey;
  title: TranslationKey;
  description: TranslationKey;
}

export const ROUTES: RouteMetadata[] = [
  {
    path: "/dashboard",
    label: "route.dashboard.label",
    title: "route.dashboard.title",
    description: "route.dashboard.description",
  },
  {
    path: "/approvals",
    label: "route.approvals.label",
    title: "route.approvals.title",
    description: "route.approvals.description",
  },
  {
    path: "/evidence",
    label: "route.evidence.label",
    title: "route.evidence.title",
    description: "route.evidence.description",
  },
  {
    path: "/portfolio",
    label: "route.portfolio.label",
    title: "route.portfolio.title",
    description: "route.portfolio.description",
  },
  {
    path: "/profile",
    label: "route.profile.label",
    title: "route.profile.title",
    description: "route.profile.description",
  },
  {
    path: "/resume",
    label: "route.resume.label",
    title: "route.resume.title",
    description: "route.resume.description",
  },
  {
    path: "/resume-studio",
    label: "route.resumeStudio.label",
    title: "route.resumeStudio.title",
    description: "route.resumeStudio.description",
  },
  {
    path: "/radar",
    label: "route.radar.label",
    title: "route.radar.title",
    description: "route.radar.description",
  },
  {
    path: "/job",
    label: "route.job.label",
    title: "route.job.title",
    description: "route.job.description",
  },
  {
    path: "/public-exams",
    label: "route.publicExams.label",
    title: "route.publicExams.title",
    description: "route.publicExams.description",
  },
  {
    path: "/sources",
    label: "route.sources.label",
    title: "route.sources.title",
    description: "route.sources.description",
  },
  {
    path: "/application-lab",
    label: "route.applicationLab.label",
    title: "route.applicationLab.title",
    description: "route.applicationLab.description",
  },
  {
    path: "/tracker",
    label: "route.tracker.label",
    title: "route.tracker.title",
    description: "route.tracker.description",
  },
  {
    path: "/interviews",
    label: "route.interviews.label",
    title: "route.interviews.title",
    description: "route.interviews.description",
  },
  {
    path: "/career",
    label: "route.career.label",
    title: "route.career.title",
    description: "route.career.description",
  },
  {
    path: "/intelligence",
    label: "route.intelligence.label",
    title: "route.intelligence.title",
    description: "route.intelligence.description",
  },
  {
    path: "/match",
    label: "route.match.label",
    title: "route.match.title",
    description: "route.match.description",
  },
  {
    path: "/ats",
    label: "route.ats.label",
    title: "route.ats.title",
    description: "route.ats.description",
  },
  {
    path: "/tailor",
    label: "route.tailor.label",
    title: "route.tailor.title",
    description: "route.tailor.description",
  },
  {
    path: "/github",
    label: "route.github.label",
    title: "route.github.title",
    description: "route.github.description",
  },
  {
    path: "/ai-quality",
    label: "route.aiQuality.label",
    title: "route.aiQuality.title",
    description: "route.aiQuality.description",
  },
  {
    path: "/settings",
    label: "route.settings.label",
    title: "route.settings.title",
    description: "route.settings.description",
  },
  {
    path: "/privacy",
    label: "route.privacy.label",
    title: "route.privacy.title",
    description: "route.privacy.description",
  },
  {
    path: "/help",
    label: "route.help.label",
    title: "route.help.title",
    description: "route.help.description",
  },
];

export function routeMetadata(pathname: string): RouteMetadata {
  return (
    ROUTES.find((route) => route.path === pathname) ?? {
      path: pathname,
      label: "route.home.label",
      title: "route.home.title",
      description: "route.home.description",
    }
  );
}
