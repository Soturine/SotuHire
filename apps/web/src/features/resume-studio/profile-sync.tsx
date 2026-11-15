import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ArrowRight, FileUp, Loader2, RefreshCcw, UserRoundCheck } from "lucide-react";
import { useId, useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ResumeImport } from "@/features/document-ingestion/resume-import";
import { ApiHttpError } from "@/lib/api/client";
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

const FIELD_LABEL: Record<string, string> = {
  title: "Título",
  subtitle: "Organização",
  content: "Texto",
  start_date: "Início",
  end_date: "Fim",
};

function invalidateOnConflict(queryClient: ReturnType<typeof useQueryClient>, error: Error): void {
  toast.error(error.message);
  // 409: the Master Resume changed in another tab; show the current one and what is still pending.
  if (error instanceof ApiHttpError && error.status === 409) {
    void queryClient.invalidateQueries({ queryKey: ["resume-studio-master"] });
    void queryClient.invalidateQueries({ queryKey: ["resume-studio-profile-updates"] });
  }
}

function toggled(set: Set<string>, id: string, on: boolean): Set<string> {
  const next = new Set(set);
  if (on) next.add(id);
  else next.delete(id);
  return next;
}

/**
 * What the Profile has that the Master Resume does not reflect yet: confirmed facts that are not
 * in it, and projected facts whose Profile text changed since (or whose Master text was edited).
 * Nothing changes until the person picks; the Profile is never written from here, and variants
 * already created keep their own content.
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
  const [refreshSelected, setRefreshSelected] = useState<Set<string>>(new Set());
  const items = updatesQ.data?.items ?? [];
  const changed = updatesQ.data?.changed ?? [];
  const chosen = selected ?? new Set(items.map((item) => item.item_id));
  const done = (resume: MasterResume, message: string) => {
    toast.success(message);
    setSelected(null);
    setRefreshSelected(new Set());
    void queryClient.invalidateQueries({ queryKey: ["resume-studio-profile-updates"] });
    onApplied(resume);
  };
  const apply = useMutation({
    mutationFn: () => api.resumeStudioApplyProfileUpdates([...chosen]),
    onSuccess: ({ resume }) =>
      done(
        resume,
        `${chosen.size} item(ns) do Perfil adicionado(s) ao Currículo Mestre. Variantes existentes não mudam.`,
      ),
    onError: (error: Error) => invalidateOnConflict(queryClient, error),
  });
  const refresh = useMutation({
    mutationFn: () => api.resumeStudioRefreshProfileFacts([...refreshSelected]),
    onSuccess: ({ resume }) =>
      done(
        resume,
        `${refreshSelected.size} item(ns) do Mestre atualizado(s) com o texto do Perfil. Variantes existentes não mudam.`,
      ),
    onError: (error: Error) => invalidateOnConflict(queryClient, error),
  });

  if (!items.length && !changed.length) return null;
  return (
    <section
      aria-labelledby={headingId}
      className="insight-surface rounded-xl border p-4 shadow-[var(--shadow-soft)] md:p-5"
      data-testid="profile-updates"
    >
      <h2 id={headingId} className="flex items-center gap-2 text-sm font-semibold">
        <RefreshCcw aria-hidden className="h-4 w-4 text-accent-strong" />O Perfil tem novidades para
        o Currículo Mestre
      </h2>
      <p className="mt-1 text-xs text-muted-foreground">
        Você escolhe o que entra. O Perfil continua sendo a origem; editar o Mestre ou uma variante
        não altera o Perfil.
      </p>

      {items.length > 0 && (
        <div className="mt-4">
          <h3 className="eyebrow text-accent-strong">{items.length} fato(s) novo(s)</h3>
          <ul className="mt-2 space-y-2">
            {items.map((item) => {
              const id = `profile-update-${item.item_id}`;
              return (
                <li key={item.item_id} className="flex items-start gap-2">
                  <Checkbox
                    id={id}
                    checked={chosen.has(item.item_id)}
                    onCheckedChange={(value) =>
                      setSelected(toggled(chosen, item.item_id, value === true))
                    }
                  />
                  <label htmlFor={id} className="text-sm leading-tight">
                    <span className="font-medium">{item.title}</span>
                    {item.subtitle && (
                      <span className="text-muted-foreground"> · {item.subtitle}</span>
                    )}
                    <span className="ml-2 rounded-full bg-surface-raised px-2 py-0.5 text-[11px] text-muted-foreground">
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
        </div>
      )}

      {changed.length > 0 && (
        <div className="mt-5" data-testid="profile-changed">
          <h3 className="eyebrow text-warning-strong">
            {changed.length} fato(s) com texto diferente do Perfil
          </h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Mudou no Perfil depois de entrar no Mestre, ou foi editado no Mestre. Marque o que deve
            seguir o Perfil; o resto fica como está.
          </p>
          <ul className="mt-2 space-y-2">
            {changed.map((item) => {
              const id = `profile-changed-${item.item_id}`;
              return (
                <li key={item.item_id} className="rounded-lg border bg-surface-raised p-3">
                  <div className="flex items-start gap-2">
                    <Checkbox
                      id={id}
                      checked={refreshSelected.has(item.item_id)}
                      onCheckedChange={(value) =>
                        setRefreshSelected(toggled(refreshSelected, item.item_id, value === true))
                      }
                    />
                    <label htmlFor={id} className="text-sm font-medium leading-tight">
                      {item.title}
                      <span className="ml-2 rounded-full bg-muted px-2 py-0.5 text-[11px] font-normal text-muted-foreground">
                        {item.section_title}
                      </span>
                    </label>
                  </div>
                  <dl className="mt-2 space-y-2 pl-6 text-xs">
                    {item.changes.map((change) => (
                      <div key={change.field} className="grid gap-1 sm:grid-cols-[5.5rem_1fr]">
                        <dt className="font-medium text-muted-foreground">
                          {FIELD_LABEL[change.field] ?? change.field}
                        </dt>
                        <dd className="grid gap-1 sm:grid-cols-2">
                          <span className="rounded-md bg-muted px-2 py-1">
                            <span className="eyebrow mr-1 text-muted-foreground">Mestre</span>
                            {change.in_master || "—"}
                          </span>
                          <span className="rounded-md bg-surface-accent px-2 py-1">
                            <span className="eyebrow mr-1 text-accent-strong">Perfil</span>
                            {change.in_profile || "—"}
                          </span>
                        </dd>
                      </div>
                    ))}
                  </dl>
                </li>
              );
            })}
          </ul>
          <Button
            size="sm"
            variant="outline"
            className="mt-3"
            disabled={!refreshSelected.size || refresh.isPending}
            onClick={() => refresh.mutate()}
            data-testid="refresh-profile-facts"
          >
            {refresh.isPending && <Loader2 aria-hidden className="h-4 w-4 animate-spin" />}
            Atualizar {refreshSelected.size} no Mestre com o texto do Perfil
          </Button>
        </div>
      )}
    </section>
  );
}
