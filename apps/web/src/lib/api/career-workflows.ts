import { useMemo } from "react";

import { pairedApiFetch } from "@/features/local-security/api-pairing";
import { useApiMode, type ApiMode } from "@/lib/api/mode";

interface Envelope<T> {
  ok: boolean;
  data?: T;
  error?: { message?: string };
}

export interface InterviewSession {
  session_id: string;
  interview_type: string;
  scheduled_at: string | null;
  organization: string;
  role: string;
  status: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface StarStory {
  story_id: string;
  title: string;
  situation: string;
  task: string;
  action: string;
  result: string;
  evidence_refs: string[];
  review_status: string;
  created_at: string;
}

export interface FollowUpDraft {
  follow_up_id: string;
  interview_session_id: string;
  follow_up_type: string;
  subject: string;
  body: string;
  status: string;
  created_at: string;
}

export interface CareerTask {
  task_id: string;
  task_type: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  due_at: string | null;
  created_at: string;
}

export interface Reminder {
  reminder_id: string;
  task_id: string;
  remind_at: string;
  title: string;
  status: string;
}

export interface CareerPlan {
  plan_id: string;
  title: string;
  status: string;
  goals: unknown[];
  certifications: unknown[];
  gap_projects: unknown[];
  created_at: string;
}

export interface CalendarExport {
  file_name: string;
  media_type: string;
  content: string;
  imported_automatically: false;
}

const now = new Date().toISOString();
const demoInterviews: InterviewSession[] = [
  {
    session_id: "demo-interview",
    interview_type: "technical",
    scheduled_at: null,
    organization: "Empresa Fictícia",
    role: "Pessoa Engenheira Backend",
    status: "preparing",
    notes: "Dados de demonstração.",
    created_at: now,
    updated_at: now,
  },
];
const demoTasks: CareerTask[] = [
  {
    task_id: "demo-task",
    task_type: "study",
    title: "Revisar evidências do portfólio",
    description: "Dados de demonstração.",
    status: "pending",
    priority: "medium",
    due_at: null,
    created_at: now,
  },
];

async function request<T>(
  mode: ApiMode,
  baseUrl: string,
  path: string,
  init: RequestInit | undefined,
  demo: T,
): Promise<T> {
  if (mode === "demo") return demo;
  const response = await pairedApiFetch(baseUrl, path, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
  });
  let envelope: Envelope<T> = { ok: false };
  try {
    envelope = (await response.json()) as Envelope<T>;
  } catch {
    // Transport errors may not include JSON.
  }
  if (!response.ok || !envelope.ok || envelope.data === undefined) {
    throw new Error(envelope.error?.message || `Erro HTTP ${response.status} em ${path}`);
  }
  return envelope.data;
}

export function makeCareerWorkflowApi(mode: ApiMode, baseUrl: string) {
  return {
    interviews: () => request(mode, baseUrl, "/interviews", undefined, demoInterviews),
    saveInterview: (payload: Partial<InterviewSession>) =>
      request(mode, baseUrl, "/interviews", post(payload), {
        ...demoInterviews[0],
        ...payload,
        session_id: crypto.randomUUID(),
      }),
    starStories: () =>
      request<StarStory[]>(mode, baseUrl, "/interviews/star-stories", undefined, []),
    saveStarStory: (payload: Partial<StarStory>) =>
      request(mode, baseUrl, "/interviews/star-stories", post(payload), {
        story_id: crypto.randomUUID(),
        title: payload.title ?? "",
        situation: payload.situation ?? "",
        task: payload.task ?? "",
        action: payload.action ?? "",
        result: payload.result ?? "",
        evidence_refs: payload.evidence_refs ?? [],
        review_status: "candidate",
        created_at: now,
      }),
    followUps: () =>
      request<FollowUpDraft[]>(mode, baseUrl, "/interviews/follow-ups", undefined, []),
    saveFollowUp: (payload: Partial<FollowUpDraft>) =>
      request(mode, baseUrl, "/interviews/follow-ups", post(payload), {
        follow_up_id: crypto.randomUUID(),
        interview_session_id: payload.interview_session_id ?? "",
        follow_up_type: payload.follow_up_type ?? "status_request",
        subject: payload.subject ?? "",
        body: payload.body ?? "",
        status: "draft",
        created_at: now,
      }),
    tasks: () => request(mode, baseUrl, "/career/tasks", undefined, demoTasks),
    saveTask: (payload: Partial<CareerTask>) =>
      request(mode, baseUrl, "/career/tasks", post(payload), {
        ...demoTasks[0],
        ...payload,
        task_id: crypto.randomUUID(),
      }),
    reminders: () => request<Reminder[]>(mode, baseUrl, "/career/reminders", undefined, []),
    saveReminder: (payload: Partial<Reminder>) =>
      request(mode, baseUrl, "/career/reminders", post(payload), {
        reminder_id: crypto.randomUUID(),
        task_id: payload.task_id ?? "",
        remind_at: payload.remind_at ?? now,
        title: payload.title ?? "",
        status: "scheduled",
      }),
    plans: () => request<CareerPlan[]>(mode, baseUrl, "/career/plans", undefined, []),
    savePlan: (payload: Partial<CareerPlan>) =>
      request(mode, baseUrl, "/career/plans", post(payload), {
        plan_id: crypto.randomUUID(),
        title: payload.title ?? "",
        status: "draft",
        goals: [],
        certifications: [],
        gap_projects: [],
        created_at: now,
      }),
    exportCalendar: (payload: Record<string, unknown>) =>
      request<CalendarExport>(mode, baseUrl, "/career/calendar/export", post(payload), {
        file_name: "sotuhire-demo.ics",
        media_type: "text/calendar; charset=utf-8",
        content: "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n",
        imported_automatically: false,
      }),
  };
}

function post(payload: unknown): RequestInit {
  return { method: "POST", body: JSON.stringify(payload) };
}

export function useCareerWorkflowApi() {
  const { mode, baseUrl } = useApiMode();
  return useMemo(() => makeCareerWorkflowApi(mode, baseUrl), [mode, baseUrl]);
}
