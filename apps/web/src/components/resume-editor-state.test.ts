import { describe, expect, it } from "vitest";
import { mockVariant } from "@/mocks/application-lab";
import {
  approximatePageCount,
  createResumeEditorState,
  resumeEditorReducer,
} from "./resume-editor-state";

describe("resume editor state", () => {
  it("keeps edits undoable and redoable", () => {
    const initial = createResumeEditorState(structuredClone(mockVariant));
    const section = initial.present.sections[0]!;
    const edited = resumeEditorReducer(initial, {
      type: "edit-section",
      sectionId: section.section_id,
      content: "Conteúdo fictício revisado",
    });
    const undone = resumeEditorReducer(edited, { type: "undo" });
    const redone = resumeEditorReducer(undone, { type: "redo" });

    expect(edited.present.sections[0]?.content).toBe("Conteúdo fictício revisado");
    expect(undone.present.sections[0]?.content).toBe(section.content);
    expect(redone.present.sections[0]?.content).toBe("Conteúdo fictício revisado");
  });

  it("reorders without deleting master content and estimates at least one page", () => {
    const variant = structuredClone(mockVariant);
    variant.sections.push({
      ...structuredClone(variant.sections[0]!),
      section_id: "section-second",
      title: "Formação",
      position: 1,
    });
    const initial = createResumeEditorState(variant);
    const moved = resumeEditorReducer(initial, {
      type: "move-section",
      sectionId: "section-second",
      direction: -1,
    });

    expect(moved.present.sections.map((section) => section.section_id)).toEqual([
      "section-demo-experience",
      "section-second",
      "section-demo-skills",
    ]);
    expect(moved.present.sections.map((section) => section.position)).toEqual([0, 1, 2]);
    expect(approximatePageCount(moved.present, "A4")).toBeGreaterThanOrEqual(1);
  });
});
