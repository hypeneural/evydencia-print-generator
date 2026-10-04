import { describe, it, expect } from "vitest";
import {
  mmToPx,
  pxToMm,
  createDraftFromTemplate,
  updateSlotMm,
  updateCanvasMm,
  validateTemplateDraft,
} from "./draft";
import type { TemplateModel } from "./types";

const mockTemplate: TemplateModel = {
  id: "calendario-2027",
  template_version: "1.0.0",
  name: "Calendário 2027",
  status: "production",
  canvas: {
    width_mm: 106.7,
    height_mm: 147.4,
    dpi: 254,
  },
  canvas_px: {
    width: 1067,
    height: 1474,
  },
  slots: [
    {
      id: "foto_principal",
      x_mm: 11.8,
      y_mm: 10.7,
      width_mm: 82.3,
      height_mm: 39.5,
      rect_px: { left: 118, top: 107, width: 823, height: 395 },
      fit: "cover",
      allow_pan: true,
      allow_zoom: true,
      allow_rotate: false,
    },
  ],
  overlay: {
    path: "assets/calendario_overlay.png",
    url: "blob:http://localhost/overlay.png",
  },
};

describe("draft domain model", () => {
  describe("mmToPx and pxToMm conversions", () => {
    it("converts 25.4 mm (1 inch) to exact DPI in pixels", () => {
      expect(mmToPx(25.4, 254)).toBe(254);
      expect(mmToPx(25.4, 300)).toBe(300);
      expect(mmToPx(25.4, 72)).toBe(72);
    });

    it("converts pixels to millimeters accurately", () => {
      expect(pxToMm(254, 254)).toBe(25.4);
      expect(pxToMm(300, 300)).toBe(25.4);
    });

    it("handles zero and negative DPI gracefully", () => {
      expect(mmToPx(10, 0)).toBe(0);
      expect(pxToMm(100, -10)).toBe(0);
    });
  });

  describe("createDraftFromTemplate", () => {
    it("creates an isolated deep copy of the template", () => {
      const draft = createDraftFromTemplate(mockTemplate);

      expect(draft.id).toBe(mockTemplate.id);
      expect(draft.name).toBe(mockTemplate.name);
      expect(draft.slots.length).toBe(1);
      expect(draft.dirty).toBe(false);

      // Verify deep clone isolation
      draft.slots[0].x_mm = 99;
      expect(mockTemplate.slots[0].x_mm).toBe(11.8);
    });
  });

  describe("updateSlotMm", () => {
    it("updates slot coordinates in mm and recalculates rect_px", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      const updated = updateSlotMm(draft, "foto_principal", {
        x_mm: 20.0,
        y_mm: 30.0,
        width_mm: 50.0,
        height_mm: 60.0,
      });

      expect(updated.dirty).toBe(true);
      const slot = updated.slots.find((s) => s.id === "foto_principal")!;
      expect(slot.x_mm).toBe(20.0);
      expect(slot.y_mm).toBe(30.0);
      expect(slot.width_mm).toBe(50.0);
      expect(slot.height_mm).toBe(60.0);

      // At 254 DPI: 20mm -> 200px, 30mm -> 300px, 50mm -> 500px, 60mm -> 600px
      expect(slot.rect_px.left).toBe(200);
      expect(slot.rect_px.top).toBe(300);
      expect(slot.rect_px.width).toBe(500);
      expect(slot.rect_px.height).toBe(600);
    });

    it("updates slot permissions and fit without corrupting position", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      const updated = updateSlotMm(draft, "foto_principal", {
        fit: "fit",
        allow_rotate: true,
      });

      const slot = updated.slots.find((s) => s.id === "foto_principal")!;
      expect(slot.fit).toBe("fit");
      expect(slot.allow_rotate).toBe(true);
      expect(slot.x_mm).toBe(11.8);
      expect(slot.rect_px.left).toBe(118);
    });
  });

  describe("updateCanvasMm", () => {
    it("updates canvas dimensions and recomputes canvas_px and slots rect_px on DPI change", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      // Change DPI to 300
      const updated = updateCanvasMm(draft, { dpi: 300 });

      expect(updated.canvas.dpi).toBe(300);
      expect(updated.canvas_px.width).toBe(mmToPx(106.7, 300));
      expect(updated.canvas_px.height).toBe(mmToPx(147.4, 300));

      const slot = updated.slots.find((s) => s.id === "foto_principal")!;
      expect(slot.rect_px.left).toBe(mmToPx(11.8, 300));
      expect(slot.rect_px.top).toBe(mmToPx(10.7, 300));
    });
  });

  describe("validateTemplateDraft", () => {
    it("passes validation for valid mock template draft", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      const result = validateTemplateDraft(draft);

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it("detects slot out of canvas bounds", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      // Place slot outside canvas width (106.7mm)
      const invalidDraft = updateSlotMm(draft, "foto_principal", {
        x_mm: 50,
        width_mm: 70, // 50 + 70 = 120 > 106.7
      });

      const result = validateTemplateDraft(invalidDraft);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.code === "SLOT_OUT_OF_BOUNDS")).toBe(true);
    });

    it("detects negative slot coordinates", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      const invalidDraft = updateSlotMm(draft, "foto_principal", {
        x_mm: -5,
      });

      const result = validateTemplateDraft(invalidDraft);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.code === "SLOT_OUT_OF_BOUNDS")).toBe(true);
    });

    it("detects duplicate slot IDs", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      draft.slots.push({
        ...draft.slots[0],
      });

      const result = validateTemplateDraft(draft);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.code === "DUPLICATE_SLOT_ID")).toBe(true);
    });

    it("detects empty slot list", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      draft.slots = [];

      const result = validateTemplateDraft(draft);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.code === "NO_SLOTS")).toBe(true);
    });

    it("detects non-positive DPI", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      draft.canvas.dpi = 0;

      const result = validateTemplateDraft(draft);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.code === "INVALID_DPI")).toBe(true);
    });

    it("emits warning for low DPI (< 150)", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      draft.canvas.dpi = 100;

      const result = validateTemplateDraft(draft);
      expect(result.valid).toBe(true);
      expect(result.warnings.length).toBeGreaterThan(0);
    });

    it("emits warning for excessively high DPI (> 600)", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      draft.canvas.dpi = 1200;

      const result = validateTemplateDraft(draft);
      expect(result.valid).toBe(true);
      expect(result.warnings.some((w) => w.includes("muito alto"))).toBe(true);
    });

    it("detects invalid slot dimensions (width <= 0 or height <= 0)", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      const invalid = updateSlotMm(draft, "foto_principal", { width_mm: 0 });

      const result = validateTemplateDraft(invalid);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.code === "INVALID_SLOT_DIMENSIONS")).toBe(true);
    });

    it("detects empty slot id", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      draft.slots[0].id = "   ";

      const result = validateTemplateDraft(draft);
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.code === "EMPTY_SLOT_ID")).toBe(true);
    });

    it("allows slot reaching exactly canvas boundary within float epsilon", () => {
      const draft = createDraftFromTemplate(mockTemplate);
      // Place slot right at canvas limit (106.7mm width, 147.4mm height)
      const validBoundary = updateSlotMm(draft, "foto_principal", {
        x_mm: 0,
        y_mm: 0,
        width_mm: 106.7,
        height_mm: 147.4,
      });

      const result = validateTemplateDraft(validBoundary);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
  });
});
