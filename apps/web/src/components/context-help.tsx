import { Link } from "@tanstack/react-router";
import { CircleHelp } from "lucide-react";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { routeMetadata } from "@/lib/route-metadata";
import { usePreferences } from "@/lib/preferences";

export function ContextHelp({ pathname }: { pathname: string }) {
  const { t } = usePreferences();
  const route = routeMetadata(pathname);
  const sections = [
    ["help.whatIs", t(route.description)],
    [
      "help.howToUse",
      ["help.shared.step.review", "help.shared.step.act", "help.shared.step.next"]
        .map((key) => t(key as "help.shared.step.review"))
        .join(" "),
    ],
    ["help.dataSources", t("help.shared.dataSources")],
    ["help.aiUsage", t("help.shared.aiUsage")],
    ["help.privacy", t("help.shared.privacy")],
    ["help.limitations", t("help.shared.limitations")],
  ] as const;

  return (
    <Sheet>
      <SheetTrigger asChild>
        <button
          type="button"
          className="grid h-9 w-9 place-items-center rounded-md border border-border bg-card text-muted-foreground hover:bg-muted"
          aria-label={t("help.open")}
        >
          <CircleHelp className="h-4 w-4" />
        </button>
      </SheetTrigger>
      <SheetContent className="w-[min(92vw,28rem)] overflow-y-auto" side="right">
        <SheetHeader>
          <SheetTitle>{t(route.title)}</SheetTitle>
          <SheetDescription>
            {t("help.drawerDescription", { page: t(route.label) })}
          </SheetDescription>
        </SheetHeader>
        <div className="mt-6 grid gap-5">
          {sections.map(([heading, body]) => (
            <section key={heading}>
              <h2 className="text-sm font-semibold">{t(heading)}</h2>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">{body}</p>
            </section>
          ))}
          <Link
            to="/help"
            className="rounded-md bg-primary px-3 py-2 text-center text-sm font-medium text-primary-foreground"
          >
            {t("help.centerLink")}
          </Link>
        </div>
      </SheetContent>
    </Sheet>
  );
}
