import type { ResumeSection, ResumeVariant } from "@/lib/api/types";

export interface ResumeEditorState {
  past: ResumeVariant[];
  present: ResumeVariant;
  future: ResumeVariant[];
  dirty: boolean;
}

export type ResumeEditorAction =
  | { type: "replace"; variant: ResumeVariant }
  | { type: "edit-meta"; field: "title" | "target_role"; value: string }
  | { type: "edit-section"; sectionId: string; content: string }
  | { type: "toggle-section"; sectionId: string }
  | { type: "move-section"; sectionId: string; direction: -1 | 1 }
  | { type: "edit-entry"; sectionId: string; entryId: string; content: string }
  | { type: "move-entry"; sectionId: string; entryId: string; direction: -1 | 1 }
  | { type: "undo" }
  | { type: "redo" }
  | { type: "saved" };

export function createResumeEditorState(variant: ResumeVariant): ResumeEditorState {
  return { past: [], present: normalizePositions(variant), future: [], dirty: false };
}

export function resumeEditorReducer(
  state: ResumeEditorState,
  action: ResumeEditorAction,
): ResumeEditorState {
  if (action.type === "replace") return createResumeEditorState(action.variant);
  if (action.type === "undo") {
    const previous = state.past.at(-1);
    if (!previous) return state;
    return {
      past: state.past.slice(0, -1),
      present: previous,
      future: [state.present, ...state.future],
      dirty: true,
    };
  }
  if (action.type === "redo") {
    const next = state.future[0];
    if (!next) return state;
    return {
      past: [...state.past, state.present],
      present: next,
      future: state.future.slice(1),
      dirty: true,
    };
  }
  if (action.type === "saved") return { ...state, dirty: false };

  let variant = structuredClone(state.present);
  if (action.type === "edit-meta") {
    variant = { ...variant, [action.field]: action.value };
  } else if (action.type === "edit-section") {
    variant.sections = variant.sections.map((section) =>
      section.section_id === action.sectionId
        ? { ...section, content: action.content, updated_at: new Date().toISOString() }
        : section,
    );
  } else if (action.type === "toggle-section") {
    variant.sections = variant.sections.map((section) =>
      section.section_id === action.sectionId
        ? { ...section, enabled: !section.enabled, updated_at: new Date().toISOString() }
        : section,
    );
  } else if (action.type === "move-section") {
    variant.sections = move(variant.sections, action.sectionId, "section_id", action.direction);
  } else if (action.type === "edit-entry") {
    variant.sections = variant.sections.map((section) =>
      section.section_id === action.sectionId
        ? {
            ...section,
            entries: section.entries.map((entry) =>
              entry.entry_id === action.entryId
                ? { ...entry, content: action.content, updated_at: new Date().toISOString() }
                : entry,
            ),
          }
        : section,
    );
  } else if (action.type === "move-entry") {
    variant.sections = variant.sections.map((section) =>
      section.section_id === action.sectionId
        ? {
            ...section,
            entries: move(section.entries, action.entryId, "entry_id", action.direction),
          }
        : section,
    );
  }
  variant = normalizePositions({ ...variant, updated_at: new Date().toISOString() });
  return {
    past: [...state.past.slice(-49), state.present],
    present: variant,
    future: [],
    dirty: true,
  };
}

export function approximatePageCount(variant: ResumeVariant, pageSize: "A4" | "Letter"): number {
  const characters = variant.sections
    .filter((section) => section.enabled)
    .reduce(
      (total, section) =>
        total +
        section.title.length +
        section.content.length +
        section.entries
          .filter((entry) => entry.enabled)
          .reduce((entryTotal, entry) => entryTotal + entry.title.length + entry.content.length, 0),
      variant.title.length + variant.target_role.length,
    );
  const capacity = pageSize === "A4" ? 3_200 : 3_400;
  return Math.max(1, Math.ceil(characters / capacity));
}

function move<T>(items: T[], id: string, key: keyof T, direction: -1 | 1): T[] {
  const current = items.findIndex((item) => String(item[key]) === id);
  const target = current + direction;
  if (current < 0 || target < 0 || target >= items.length) return items;
  const result = [...items];
  [result[current], result[target]] = [result[target]!, result[current]!];
  return result;
}

function normalizePositions(variant: ResumeVariant): ResumeVariant {
  return {
    ...variant,
    sections: variant.sections.map(
      (section, sectionPosition): ResumeSection => ({
        ...section,
        position: sectionPosition,
        entries: section.entries.map((entry, entryPosition) => ({
          ...entry,
          position: entryPosition,
        })),
      }),
    ),
  };
}
