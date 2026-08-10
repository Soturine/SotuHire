import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, CheckCircle2, Compass, Eye, ShieldCheck } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { v2Api } from "./api";
import { useApiMode } from "@/lib/api/mode";
import { usePreferences } from "@/lib/preferences";

export function CopilotDrawer({ pathname }: { pathname: string }) {
  const { mode, baseUrl } = useApiMode();
  const { locale } = usePreferences();
  const pt = locale === "pt-BR";
  const client = useQueryClient();
  const [open, setOpen] = useState(false);
  const state = useQuery({
    queryKey: ["v2", "career-state", mode, baseUrl],
    queryFn: () => v2Api(mode, baseUrl).careerState(),
    enabled: open,
  });
  const propose = useMutation({
    mutationFn: (actionId: string) =>
      v2Api(mode, baseUrl).createProposal({
        tool_id: "create_task",
        input: {
          title: pt ? "Revisar recomendação do Copilot" : "Review Copilot recommendation",
          task_type: "custom",
          priority: "medium",
        },
        reason:
          state.data?.recommendation_candidates.find((item) => item.action_id === actionId)
            ?.reason ?? "User-requested review",
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["v2", "approvals", mode, baseUrl] }),
  });
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          aria-label={pt ? "Abrir Copilot contextual" : "Open contextual Copilot"}
        >
          <Bot /> <span className="hidden md:inline">Copilot</span>
        </Button>
      </SheetTrigger>
      <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Compass className="text-accent" />
            {pt ? "Copilot sob sua aprovação" : "Human-approved Copilot"}
          </SheetTitle>
          <SheetDescription>
            {pt
              ? `Contexto atual: ${pathname}. Ele propõe; você decide e executa.`
              : `Current context: ${pathname}. It proposes; you decide and execute.`}
          </SheetDescription>
        </SheetHeader>
        <div className="mt-6 space-y-5">
          <div className="rounded-xl border bg-muted/30 p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Eye className="h-4 w-4 text-accent" />
              {pt ? "O que foi considerado" : "What was considered"}
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              {state.data?.profile_summary ??
                (pt ? "Carregando contexto mínimo…" : "Loading minimal context…")}
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              <ShieldCheck className="mr-1 inline h-3.5 w-3.5" />
              {pt
                ? "Dados sensíveis e claims não confirmados não são enviados externamente por padrão."
                : "Sensitive data and unconfirmed claims are not externally shared by default."}
            </p>
          </div>
          <div>
            <h3 className="mb-3 font-semibold">
              {pt ? "Sugestões no contexto" : "Contextual suggestions"}
            </h3>
            <div className="space-y-3">
              {state.data?.recommendation_candidates.slice(0, 4).map((action) => (
                <article key={action.action_id} className="rounded-xl border p-4">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                    <div className="min-w-0 flex-1">
                      <h4 className="text-sm font-semibold">{action.type.replaceAll("_", " ")}</h4>
                      <p className="mt-1 text-xs text-muted-foreground">{action.reason}</p>
                      <p className="mt-2 text-xs">
                        <strong>{pt ? "Impacto" : "Impact"}:</strong> {action.impact}
                      </p>
                      <Button
                        className="mt-3"
                        size="sm"
                        variant="outline"
                        onClick={() => propose.mutate(action.action_id)}
                        disabled={propose.isPending}
                      >
                        {pt ? "Criar proposta" : "Create proposal"}
                      </Button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
