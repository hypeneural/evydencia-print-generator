import { describe, it, expect } from "vitest";
import { createHistoryManager } from "./history";
import type { EditStateModel } from "./types";

describe("HistoryManager", () => {
  const initial: EditStateModel = {
    template_id: "test",
    template_version: "1.0",
    slot_edits: {
      s1: { source_id: "a", pan_x_norm: 0, pan_y_norm: 0, scale: 1, rotation_deg: 0 },
    },
  };

  it("handles push, undo, and redo correctly", () => {
    const h = createHistoryManager(initial);
    expect(h.canUndo).toBe(false);
    expect(h.canRedo).toBe(false);

    const step1: EditStateModel = {
      ...initial,
      slot_edits: {
        s1: { source_id: "a", pan_x_norm: 0.5, pan_y_norm: 0, scale: 1, rotation_deg: 0 },
      },
    };
    h.push(step1);
    expect(h.canUndo).toBe(true);
    expect(h.canRedo).toBe(false);
    expect(h.present.slot_edits.s1.pan_x_norm).toBe(0.5);

    // Undo
    const undone = h.undo();
    expect(undone?.slot_edits.s1.pan_x_norm).toBe(0);
    expect(h.canUndo).toBe(false);
    expect(h.canRedo).toBe(true);

    // Redo
    const redone = h.redo();
    expect(redone?.slot_edits.s1.pan_x_norm).toBe(0.5);
    expect(h.canUndo).toBe(true);
    expect(h.canRedo).toBe(false);
  });

  it("clears redo stack on new push", () => {
    const h = createHistoryManager(initial);
    const step1 = { ...initial, template_id: "step1" };
    const step2 = { ...initial, template_id: "step2" };

    h.push(step1);
    h.undo();
    expect(h.canRedo).toBe(true);

    h.push(step2);
    expect(h.canRedo).toBe(false);
  });
});
