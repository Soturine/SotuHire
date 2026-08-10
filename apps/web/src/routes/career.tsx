import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Bell, CalendarPlus, CheckCircle2, Download, Plus } from "lucide-react";
import { useState, type FormEvent } from "react";

import { AppShell } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";
import { useCareerWorkflowApi } from "@/lib/api/career-workflows";
import { useApiMode } from "@/lib/api/mode";
import { usePreferences } from "@/lib/preferences";

export const Route = createFileRoute("/career")({
  head: () => ({ meta: [{ title: "Plano de carreira — SotuHire" }] }),
  component: CareerPage,
});

function CareerPage() {
  const { t, format } = usePreferences();
  const { mode, baseUrl } = useApiMode();
  const api = useCareerWorkflowApi();
  const queryClient = useQueryClient();
  const tasks = useQuery({ queryKey: ["career-tasks", mode, baseUrl], queryFn: api.tasks });
  const reminders = useQuery({
    queryKey: ["career-reminders", mode, baseUrl],
    queryFn: api.reminders,
  });
  const plans = useQuery({ queryKey: ["career-plans", mode, baseUrl], queryFn: api.plans });
  const [taskTitle, setTaskTitle] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [reminderTitle, setReminderTitle] = useState("");
  const [remindAt, setRemindAt] = useState("");
  const [planTitle, setPlanTitle] = useState("");

  const saveTask = useMutation({
    mutationFn: () =>
      api.saveTask({ title: taskTitle, task_type: "custom", due_at: dueAt || null }),
    onSuccess: async () => {
      setTaskTitle("");
      setDueAt("");
      await queryClient.invalidateQueries({ queryKey: ["career-tasks", mode, baseUrl] });
    },
  });
  const saveReminder = useMutation({
    mutationFn: () =>
      api.saveReminder({
        task_id: tasks.data?.[0]?.task_id ?? "",
        title: reminderTitle,
        remind_at: new Date(remindAt).toISOString(),
      }),
    onSuccess: async () => {
      setReminderTitle("");
      setRemindAt("");
      await queryClient.invalidateQueries({ queryKey: ["career-reminders", mode, baseUrl] });
    },
  });
  const savePlan = useMutation({
    mutationFn: () => api.savePlan({ title: planTitle }),
    onSuccess: async () => {
      setPlanTitle("");
      await queryClient.invalidateQueries({ queryKey: ["career-plans", mode, baseUrl] });
    },
  });

  async function downloadTaskCalendar(taskId: string, title: string, startsAt: string) {
    const result = await api.exportCalendar({
      entity_type: "career_task",
      entity_id: taskId,
      title,
      starts_at: startsAt,
    });
    const url = URL.createObjectURL(new Blob([result.content], { type: result.media_type }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = result.file_name;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <AppShell title={t("route.career.title")} description={t("route.career.description")}>
      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard
          title="Próximas ações"
          description="Tarefas locais e explicitamente revisáveis."
        >
          <form
            className="grid gap-3 sm:grid-cols-[1fr_auto]"
            onSubmit={(event: FormEvent) => {
              event.preventDefault();
              saveTask.mutate();
            }}
          >
            <Field label="Tarefa" value={taskTitle} onChange={setTaskTitle} required />
            <Field label="Prazo opcional" value={dueAt} onChange={setDueAt} type="datetime-local" />
            <button className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground sm:col-span-2">
              <Plus className="h-4 w-4" /> Adicionar tarefa
            </button>
          </form>
          <div className="mt-5 grid gap-2">
            {tasks.data?.map((task) => (
              <article
                key={task.task_id}
                className="flex items-start gap-3 rounded-lg border border-border p-3"
              >
                <CheckCircle2 className="mt-0.5 h-4 w-4 text-accent" />
                <div className="min-w-0 flex-1">
                  <strong className="text-sm">{task.title}</strong>
                  <p className="text-xs text-muted-foreground">
                    {task.priority} · {task.status}
                    {task.due_at ? ` · ${format.date(task.due_at)}` : ""}
                  </p>
                </div>
                {task.due_at && (
                  <button
                    type="button"
                    onClick={() => downloadTaskCalendar(task.task_id, task.title, task.due_at!)}
                    className="grid h-8 w-8 place-items-center rounded-md border border-input hover:bg-muted"
                    aria-label="Baixar evento ICS"
                    title="Baixar ICS; nenhuma agenda é alterada automaticamente"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                )}
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          title="Lembretes"
          description="Salvos localmente; sem adicionar eventos automaticamente."
        >
          <form
            className="grid gap-3"
            onSubmit={(event) => {
              event.preventDefault();
              saveReminder.mutate();
            }}
          >
            <Field label="Título" value={reminderTitle} onChange={setReminderTitle} required />
            <Field
              label="Data e hora"
              value={remindAt}
              onChange={setRemindAt}
              type="datetime-local"
              required
            />
            <button className="inline-flex items-center justify-center gap-2 rounded-md border border-input px-3 py-2 text-sm font-medium hover:bg-muted">
              <Bell className="h-4 w-4" /> Agendar lembrete local
            </button>
          </form>
          <div className="mt-5 grid gap-2">
            {reminders.data?.map((reminder) => (
              <article key={reminder.reminder_id} className="rounded-lg bg-muted/60 p-3">
                <strong className="text-sm">{reminder.title}</strong>
                <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                  <CalendarPlus className="h-3.5 w-3.5" />
                  {format.date(reminder.remind_at, { dateStyle: "medium", timeStyle: "short" })}
                </p>
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard
          className="xl:col-span-2"
          title="Planos de carreira"
          description="Metas, certificações e projetos de lacuna permanecem candidatos até sua revisão."
        >
          <form
            className="flex flex-col gap-3 sm:flex-row sm:items-end"
            onSubmit={(event) => {
              event.preventDefault();
              savePlan.mutate();
            }}
          >
            <div className="flex-1">
              <Field label="Nome do plano" value={planTitle} onChange={setPlanTitle} required />
            </div>
            <button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
              Criar plano
            </button>
          </form>
          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {plans.data?.map((plan) => (
              <article key={plan.plan_id} className="rounded-lg border border-border p-4">
                <strong className="text-sm">{plan.title}</strong>
                <p className="mt-1 text-xs text-muted-foreground">
                  {plan.status} · {plan.goals.length} meta(s) · {plan.gap_projects.length}{" "}
                  projeto(s)
                </p>
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
  type = "text",
  required,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
}) {
  return (
    <label className="grid gap-1.5 text-sm font-medium">
      {label}
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        className="rounded-md border border-input bg-background px-3 py-2 text-sm"
      />
    </label>
  );
}
