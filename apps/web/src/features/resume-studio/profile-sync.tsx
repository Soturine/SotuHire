import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ArrowRight, FileUp, Loader2, UserRoundCheck } from "lucide-react";
import { useId, useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ResumeImport } from "@/features/document-ingestion/resume-import";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import type { MasterResume } from "@/lib/api/types";
import { toast } from "@/lib/notify";

/**
 * First use of the Resume Studio: the Master Resume is derived from the Universal Profile (the user
 * already confirmed those facts there) or, as an alternative, imported from a resume file.
 */
export function MasterOnboarding({ onCreated }: { onCreated: (resume: MasterResume) => void }) {
  const api = useApi();
  const { mode } = useApiMode();
  const fromProfile = useMutation({
    mutationFn: () => api.resumeStudioMasterFromProfile(),
    onSuccess: ({ resume }) => {
      toast.success(
        mode === "demo"
          ? "DEMO: Currículo Mestre fictício montado a partir do Perfil."
          : `Currículo Mestre montado com ${resume.source_profile_item_ids.length} item(ns) confirmado(s) do Perfil.`,
      );
      onCreated(resume);
    },
  });

  return (
    <section aria-labelledby="master-onboarding-title" className="space-y-4">
      <div>
        <h2 id="master-onboarding-title" className="text-lg font-semibold tracking-tight">
          Seu Currículo Mestre ainda não existe
        </h2>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          Ele é o documento base das variantes por vaga. Use o que você já confirmou no Perfil; só
          fatos confirmados entram, cada um com a origem registrada.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-accent/40 bg-card p-5">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <UserRoundCheck aria-hidden className="h-4 w-4 text-accent-strong" />
            Montar a partir do Perfil Universal
          </div>
          <p className="mt-2 text-sm text-muted-foreground">
            Experiências, formação, projetos, certificações, competências e idiomas confirmados
            viram seções do currículo. Itens não confirmados ou sensíveis ficam de fora.
          </p>
          {fromProfile.isError && (
            <p role="alert" className="mt-3 text-sm text-destructive-strong">
              {fromProfile.error.message}{" "}
              <Link to="/profile" className="font-medium underline underline-offset-2">
                Abrir o Perfil
              </Link>
            </p>
          )}
          <Button
            className="mt-4"
            onClick={() => fromProfile.mutate()}
            disabled={fromProfile.isPending}
            data-testid="master-from-profile"
          >
            {fromProfile.isPending ? (
              <Loader2 aria-hidden className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowRight aria-hidden className="h-4 w-4" />
            )}
            Montar Currículo Mestre
          </Button>
        </div>
        <div className="rounded-xl border bg-card p-5">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <FileUp aria-hidden className="h-4 w-4 text-muted-foreground" />
            Ou importar um currículo existente
          </div>
          <p className="mt-2 mb-3 text-sm text-muted-foreground">
            PDF, DOCX, TXT ou JSON Resume. Você revisa cada trecho antes de salvar.
          </p>
          <ResumeImport onImported={onCreated} />
        </div>
      </div>
    </section>
  );
}

/**
 * Confirmed profile facts the Master Resume does not have yet. Nothing changes until the user picks
 * which ones to add; variants already created keep their own content.
 */
export function ProfileUpdatesPanel({ onApplied }: { onApplied: (resume: MasterResume) => void }) {
  const api = useApi();
  const { mode, baseUrl } = useApiMode();
  const queryClient = useQueryClient();
  const headingId = useId();
  const updatesQ = useQuery({
    queryKey: ["resume-studio-profile-updates", mode, baseUrl],
    queryFn: () => api.resumeStudioProfileUpdates(),
  });
  const [selected, setSelected] = useState<Set<string> | null>(null);
  const items = updatesQ.data?.items ?? [];
  const chosen = selected ?? new Set(items.map((item) => item.item_id));
  const apply = useMutation({
    mutationFn: () => api.resumeStudioApplyProfileUpdates([...chosen]),
    onSuccess: ({ resume }) => {
      toast.success(
        `${chosen.size} item(ns) do Perfil adicionado(s) ao Currículo Mestre. Variantes existentes não mudam.`,
      );
      setSelected(null);
      void queryClient.invalidateQueries({ queryKey: ["resume-studio-profile-updates"] });
      onApplied(resume);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!items.length) return null;
  return (
    <section
      aria-labelledby={headingId}
      className="rounded-xl border border-accent/40 bg-accent/5 p-4"
      data-testid="profile-updates"
    >
      <h2 id={headingId} className="text-sm font-semibold">
        {items.length} fato(s) confirmado(s) no Perfil ainda não estão no Currículo Mestre
      </h2>
      <p className="mt-1 text-xs text-muted-foreground">
        Escolha o que entra. O Perfil continua sendo a origem; editar uma variante não altera o
        Perfil.
      </p>
      <ul className="mt-3 space-y-2">
        {items.map((item) => {
          const id = `profile-update-${item.item_id}`;
          return (
            <li key={item.item_id} className="flex items-start gap-2">
              <Checkbox
                id={id}
                checked={chosen.has(item.item_id)}
                onCheckedChange={(value) => {
                  const next = new Set(chosen);
                  if (value === true) next.add(item.item_id);
                  else next.delete(item.item_id);
                  setSelected(next);
                }}
              />
              <label htmlFor={id} className="text-sm leading-tight">
                <span className="font-medium">{item.title}</span>
                {item.subtitle && <span className="text-muted-foreground"> · {item.subtitle}</span>}
                <span className="ml-2 rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
                  {item.section_title}
                </span>
              </label>
            </li>
          );
        })}
      </ul>
      <Button
        size="sm"
        className="mt-3"
        disabled={!chosen.size || apply.isPending}
        onClick={() => apply.mutate()}
        data-testid="apply-profile-updates"
      >
        {apply.isPending && <Loader2 aria-hidden className="h-4 w-4 animate-spin" />}
        Adicionar {chosen.size} ao Currículo Mestre
      </Button>
    </section>
  );
}
