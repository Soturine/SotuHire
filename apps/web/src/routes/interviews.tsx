import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { CalendarCheck, MessageSquareText, Plus, Sparkles } from "lucide-react";
import { useState, type FormEvent } from "react";

import { AppShell } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";
import { useCareerWorkflowApi } from "@/lib/api/career-workflows";
import { useApiMode } from "@/lib/api/mode";
import { usePreferences } from "@/lib/preferences";

export const Route = createFileRoute("/interviews")({
  head: () => ({ meta: [{ title: "Entrevistas — SotuHire" }] }),
  component: InterviewsPage,
});

function InterviewsPage() {
  const { t, format } = usePreferences();
  const { mode, baseUrl } = useApiMode();
  const api = useCareerWorkflowApi();
  const queryClient = useQueryClient();
  const interviews = useQuery({
    queryKey: ["interviews", mode, baseUrl],
    queryFn: api.interviews,
  });
  const stories = useQuery({
    queryKey: ["star-stories", mode, baseUrl],
    queryFn: api.starStories,
  });
  const followUps = useQuery({
    queryKey: ["follow-ups", mode, baseUrl],
    queryFn: api.followUps,
  });
  const [organization, setOrganization] = useState("");
  const [role, setRole] = useState("");
  const [storyTitle, setStoryTitle] = useState("");
  const [storyEvidence, setStoryEvidence] = useState("");
  const [followSubject, setFollowSubject] = useState("");
  const [followBody, setFollowBody] = useState("");

  const saveInterview = useMutation({
    mutationFn: () =>
      api.saveInterview({ organization, role, interview_type: "other", status: "draft" }),
    onSuccess: async () => {
      setOrganization("");
      setRole("");
      await queryClient.invalidateQueries({ queryKey: ["interviews", mode, baseUrl] });
    },
  });
  const saveStory = useMutation({
    mutationFn: () =>
      api.saveStarStory({
        title: storyTitle,
        evidence_refs: storyEvidence ? [storyEvidence] : [],
      }),
    onSuccess: async () => {
      setStoryTitle("");
      setStoryEvidence("");
      await queryClient.invalidateQueries({ queryKey: ["star-stories", mode, baseUrl] });
    },
  });
  const saveFollowUp = useMutation({
    mutationFn: () =>
      api.saveFollowUp({
        interview_session_id: interviews.data?.[0]?.session_id ?? "",
        follow_up_type: "interview_follow_up",
        subject: followSubject,
        body: followBody,
      }),
    onSuccess: async () => {
      setFollowSubject("");
      setFollowBody("");
      await queryClient.invalidateQueries({ queryKey: ["follow-ups", mode, baseUrl] });
    },
  });

  return (
    <AppShell title={t("route.interviews.title")} description={t("route.interviews.description")}>
      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard
          title="Entrevistas"
          description="Registre o encontro antes de preparar perguntas e respostas."
        >
          <form
            className="grid gap-3 sm:grid-cols-2"
            onSubmit={(event: FormEvent) => {
              event.preventDefault();
              saveInterview.mutate();
            }}
          >
            <Field label="Organização" value={organization} onChange={setOrganization} required />
            <Field label="Cargo" value={role} onChange={setRole} required />
            <button
              type="submit"
              disabled={saveInterview.isPending}
              className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground sm:col-span-2"
            >
              <Plus className="h-4 w-4" /> Nova entrevista
            </button>
          </form>
          <div className="mt-5 grid gap-3">
            {interviews.data?.map((interview) => (
              <article key={interview.session_id} className="rounded-lg border border-border p-3">
                <div className="flex items-center justify-between gap-3">
                  <strong className="text-sm">{interview.role || "Cargo a confirmar"}</strong>
                  <span className="rounded-full bg-muted px-2 py-1 text-xs">
                    {interview.status}
                  </span>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{interview.organization}</p>
                {interview.scheduled_at && (
                  <p className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
                    <CalendarCheck className="h-3.5 w-3.5" />
                    {format.date(interview.scheduled_at, {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </p>
                )}
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          title="Histórias STAR"
          description="Resultados e números só devem ser usados com evidências verificáveis."
        >
          <form
            className="grid gap-3"
            onSubmit={(event) => {
              event.preventDefault();
              saveStory.mutate();
            }}
          >
            <Field label="Título" value={storyTitle} onChange={setStoryTitle} required />
            <Field
              label="Referência da evidência"
              value={storyEvidence}
              onChange={setStoryEvidence}
              placeholder="profile-item://..."
            />
            <button className="inline-flex items-center justify-center gap-2 rounded-md border border-input px-3 py-2 text-sm font-medium hover:bg-muted">
              <Sparkles className="h-4 w-4" /> Salvar rascunho STAR
            </button>
          </form>
          <div className="mt-5 grid gap-2">
            {stories.data?.map((story) => (
              <article key={story.story_id} className="rounded-lg bg-muted/60 p-3 text-sm">
                <strong>{story.title}</strong>
                <p className="mt-1 text-xs text-muted-foreground">
                  {story.evidence_refs.length} evidência(s) · {story.review_status}
                </p>
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          className="xl:col-span-2"
          title="Follow-up"
          description="O SotuHire cria e salva rascunhos; você revisa, copia e envia manualmente."
        >
          <form
            className="grid gap-3"
            onSubmit={(event) => {
              event.preventDefault();
              saveFollowUp.mutate();
            }}
          >
            <Field label="Assunto" value={followSubject} onChange={setFollowSubject} required />
            <label className="grid gap-1.5 text-sm font-medium">
              Mensagem
              <textarea
                value={followBody}
                onChange={(event) => setFollowBody(event.target.value)}
                required
                rows={4}
                className="rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </label>
            <button className="inline-flex w-fit items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground">
              <MessageSquareText className="h-4 w-4" /> Salvar rascunho
            </button>
          </form>
          <div className="mt-5 grid gap-2 md:grid-cols-2">
            {followUps.data?.map((draft) => (
              <article key={draft.follow_up_id} className="rounded-lg border border-border p-3">
                <strong className="text-sm">{draft.subject || "Sem assunto"}</strong>
                <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{draft.body}</p>
                <span className="mt-2 inline-block text-xs text-muted-foreground">
                  {draft.status} · envio manual
                </span>
              </article>
            ))}
          </div>
        </SectionCard>
      </div>
    </AppShell>
  );
}

function Field({
  label,
  value,
  onChange,
  required,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  placeholder?: string;
}) {
  return (
    <label className="grid gap-1.5 text-sm font-medium">
      {label}
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        placeholder={placeholder}
        className="rounded-md border border-input bg-background px-3 py-2 text-sm"
      />
    </label>
  );
}
