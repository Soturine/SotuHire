import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, BookOpen, Eye, Layers3 } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { v2Api } from "@/features/career-copilot/api";
import { useApiMode } from "@/lib/api/mode";
import { usePreferences } from "@/lib/preferences";

export const Route = createFileRoute("/portfolio")({ component: Portfolio });

function Portfolio() {
  const { mode, baseUrl } = useApiMode();
  const { locale } = usePreferences();
  const pt = locale === "pt-BR";
  const items = useQuery({
    queryKey: ["v2", "portfolio", mode, baseUrl],
    queryFn: () => v2Api(mode, baseUrl).portfolio(),
  });
  return (
    <AppShell
      title={pt ? "Portfólio" : "Portfolio"}
      description={
        pt
          ? "Projetos, pesquisa, design, ensino e produção com evidências."
          : "Projects, research, design, teaching, and work backed by evidence."
      }
    >
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="grid gap-4 md:grid-cols-3">
          <Summary
            icon={Layers3}
            value={items.data?.length ?? 0}
            label={pt ? "itens multidisciplinares" : "multidisciplinary items"}
          />
          <Summary
            icon={BookOpen}
            value={items.data?.filter((item) => item.evidence_refs.length).length ?? 0}
            label={pt ? "com evidência vinculada" : "with linked evidence"}
          />
          <Summary
            icon={Eye}
            value={items.data?.filter((item) => item.visibility !== "private").length ?? 0}
            label={pt ? "exportáveis" : "exportable"}
          />
        </div>
        <div className="portfolio-grid grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {items.data?.map((item, index) => (
            <article
              key={item.portfolio_item_id}
              className="group overflow-hidden rounded-2xl border bg-card shadow-[var(--shadow-soft)]"
            >
              <div className={`portfolio-cover portfolio-cover-${index % 3}`}>
                <span>{item.type.replaceAll("_", " ")}</span>
              </div>
              <div className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">{item.title}</h2>
                    <p className="mt-1 text-sm text-muted-foreground">{item.role}</p>
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <p className="mt-4 text-sm">{item.description}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {item.skills.map((skill) => (
                    <span key={skill} className="rounded-full border px-2 py-1 text-xs">
                      {skill}
                    </span>
                  ))}
                </div>
                <div className="mt-5 flex items-center justify-between border-t pt-4 text-xs text-muted-foreground">
                  <span>
                    {item.evidence_refs.length} {pt ? "evidência(s)" : "evidence link(s)"}
                  </span>
                  <span>{item.visibility}</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </AppShell>
  );
}

function Summary({
  icon: Icon,
  value,
  label,
}: {
  icon: typeof Layers3;
  value: number;
  label: string;
}) {
  return (
    <div className="rounded-2xl border bg-card p-5">
      <Icon className="h-5 w-5 text-accent" />
      <div className="mt-4 text-3xl font-semibold">{value}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
    </div>
  );
}
