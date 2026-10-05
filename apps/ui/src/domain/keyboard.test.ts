import { describe, it, expect } from "vitest";
import { isTextEditingTarget, shouldHandleDeletePhoto } from "./keyboard";
import { removeSlotPhoto } from "./slot_assignment";
import { createHistoryManager } from "./history";
import type { EditStateModel } from "./types";

describe("keyboard domain", () => {
  describe("isTextEditingTarget", () => {
    it("returns true for input, textarea, and select elements", () => {
      expect(isTextEditingTarget({ tagName: "INPUT" })).toBe(true);
      expect(isTextEditingTarget({ tagName: "input" })).toBe(true);
      expect(isTextEditingTarget({ tagName: "TEXTAREA" })).toBe(true);
      expect(isTextEditingTarget({ tagName: "SELECT" })).toBe(true);
    });

    it("returns true for contenteditable targets", () => {
      expect(isTextEditingTarget({ tagName: "DIV", isContentEditable: true })).toBe(true);
      expect(
        isTextEditingTarget({
          tagName: "SPAN",
          closest: (sel) => (sel.includes("contenteditable") ? {} : null),
        })
      ).toBe(true);
    });

    it("returns false for non-text elements (canvas, button, body, div)", () => {
      expect(isTextEditingTarget({ tagName: "CANVAS" })).toBe(false);
      expect(isTextEditingTarget({ tagName: "BUTTON" })).toBe(false);
      expect(isTextEditingTarget({ tagName: "DIV" })).toBe(false);
      expect(isTextEditingTarget(null)).toBe(false);
      expect(isTextEditingTarget(undefined)).toBe(false);
    });
  });

  describe("shouldHandleDeletePhoto", () => {
    const baseCtx = {
      key: "Delete",
      ctrlKey: false,
      altKey: false,
      metaKey: false,
      shiftKey: false,
      target: { tagName: "CANVAS" },
      mode: "operator" as const,
      templateId: "chaveiro-3x4",
      activeSlotId: "slot_01",
      hasPhotoInActiveSlot: true,
    };

    it("accepts Delete on Chaveiro with active photo in operator mode", () => {
      expect(shouldHandleDeletePhoto(baseCtx)).toBe(true);
    });

    it("accepts Delete on Globo de Neve with active photo in operator mode", () => {
      expect(
        shouldHandleDeletePhoto({
          ...baseCtx,
          templateId: "globo-neve",
          activeSlotId: "foto_1",
        })
      ).toBe(true);
    });

    it("rejects Delete on Calendario (single slot product)", () => {
      expect(
        shouldHandleDeletePhoto({
          ...baseCtx,
          templateId: "calendario-2027",
          activeSlotId: "foto_principal",
        })
      ).toBe(false);
    });

    it("rejects when mode is manager", () => {
      expect(
        shouldHandleDeletePhoto({
          ...baseCtx,
          mode: "manager",
        })
      ).toBe(false);
    });

    it("rejects when slot is empty (no photo)", () => {
      expect(
        shouldHandleDeletePhoto({
          ...baseCtx,
          hasPhotoInActiveSlot: false,
        })
      ).toBe(false);
    });

    it("rejects when no active slot", () => {
      expect(
        shouldHandleDeletePhoto({
          ...baseCtx,
          activeSlotId: null,
        })
      ).toBe(false);
    });

    it("rejects when modifiers are pressed (Ctrl+Delete, Alt+Delete, etc.)", () => {
      expect(shouldHandleDeletePhoto({ ...baseCtx, ctrlKey: true })).toBe(false);
      expect(shouldHandleDeletePhoto({ ...baseCtx, altKey: true })).toBe(false);
      expect(shouldHandleDeletePhoto({ ...baseCtx, metaKey: true })).toBe(false);
    });

    it("rejects when typing inside input / textarea / contenteditable", () => {
      expect(
        shouldHandleDeletePhoto({
          ...baseCtx,
          target: { tagName: "INPUT" },
        })
      ).toBe(false);
      expect(
        shouldHandleDeletePhoto({
          ...baseCtx,
          target: { tagName: "DIV", isContentEditable: true },
        })
      ).toBe(false);
    });

    it("rejects other keys (Backspace, Escape, etc.)", () => {
      expect(shouldHandleDeletePhoto({ ...baseCtx, key: "Backspace" })).toBe(false);
      expect(shouldHandleDeletePhoto({ ...baseCtx, key: "Escape" })).toBe(false);
    });
  });

  describe("Delete + Undo / History Integration", () => {
    it("Delete removes active slot photo and Ctrl+Z restores exact transform", () => {
      const initialEditState: EditStateModel = {
        template_id: "chaveiro-3x4",
        template_version: "1.0.0",
        slot_edits: {
          slot_01: {
            source_id: "photo_123",
            pan_x_norm: 0.15,
            pan_y_norm: -0.25,
            scale: 1.8,
            rotation_deg: 90,
          },
          slot_02: {
            source_id: "photo_456",
            pan_x_norm: 0,
            pan_y_norm: 0,
            scale: 1,
            rotation_deg: 0,
          },
        },
      };

      const history = createHistoryManager(initialEditState);

      // Perform Delete on slot_01
      const nextEdits = removeSlotPhoto(initialEditState.slot_edits, "slot_01");
      expect(nextEdits).not.toBeNull();
      const afterDeleteState: EditStateModel = {
        ...initialEditState,
        slot_edits: nextEdits!,
      };
      history.push(afterDeleteState);

      expect(afterDeleteState.slot_edits["slot_01"]).toBeUndefined();
      expect(afterDeleteState.slot_edits["slot_02"]).toEqual(
        initialEditState.slot_edits["slot_02"]
      );

      // Undo (Ctrl+Z)
      const restored = history.undo();
      expect(restored).not.toBeNull();
      expect(restored!.slot_edits["slot_01"]).toEqual({
        source_id: "photo_123",
        pan_x_norm: 0.15,
        pan_y_norm: -0.25,
        scale: 1.8,
        rotation_deg: 90,
      });
      expect(restored!.slot_edits["slot_02"]).toEqual(
        initialEditState.slot_edits["slot_02"]
      );
    });
  });
});
