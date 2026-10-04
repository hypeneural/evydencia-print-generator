import type { PixelRect, TemplateModel } from "./types";

export interface DraftSlot {
  id: string;
  x_mm: number;
  y_mm: number;
  width_mm: number;
  height_mm: number;
  rect_px: PixelRect;
  fit: "cover" | "fit" | string;
  allow_pan: boolean;
  allow_zoom: boolean;
  allow_rotate: boolean;
}

export interface DraftOverlay {
  path: string;
  url?: string;
  required?: boolean;
}

export interface DraftCanvas {
  width_mm: number;
  height_mm: number;
  dpi: number;
}

export interface TemplateDraft {
  id: string;
  template_version: string;
  name: string;
  status: string;
  canvas: DraftCanvas;
  canvas_px: {
    width: number;
    height: number;
  };
  slots: DraftSlot[];
  overlay: DraftOverlay | null;
  dirty?: boolean;
}

export interface DraftValidationError {
  code:
    | "INVALID_DPI"
    | "INVALID_CANVAS_DIMENSIONS"
    | "NO_SLOTS"
    | "DUPLICATE_SLOT_ID"
    | "EMPTY_SLOT_ID"
    | "INVALID_SLOT_DIMENSIONS"
    | "SLOT_OUT_OF_BOUNDS";
  message: string;
  slot_id?: string;
}

export interface DraftValidationResult {
  valid: boolean;
  errors: DraftValidationError[];
  warnings: string[];
}

/**
 * Standard deterministic conversion from millimeters to pixels at a given DPI.
 * Rounding matches print engine specification: Math.round((mm / 25.4) * dpi).
 */
export function mmToPx(mm: number, dpi: number): number {
  if (dpi <= 0) return 0;
  return Math.round((mm / 25.4) * dpi);
}

/**
 * Standard conversion from pixels to millimeters at a given DPI.
 * Returns value rounded to 2 decimal places.
 */
export function pxToMm(px: number, dpi: number): number {
  if (dpi <= 0) return 0;
  const mm = (px * 25.4) / dpi;
  return Math.round(mm * 100) / 100;
}

/**
 * Creates an in-memory mutable TemplateDraft by deep-cloning an immutable TemplateModel.
 */
export function createDraftFromTemplate(template: TemplateModel): TemplateDraft {
  return {
    id: template.id,
    template_version: template.template_version,
    name: template.name,
    status: template.status,
    canvas: {
      width_mm: template.canvas.width_mm,
      height_mm: template.canvas.height_mm,
      dpi: template.canvas.dpi,
    },
    canvas_px: {
      width: template.canvas_px.width,
      height: template.canvas_px.height,
    },
    slots: template.slots.map((s) => ({
      id: s.id,
      x_mm: s.x_mm,
      y_mm: s.y_mm,
      width_mm: s.width_mm,
      height_mm: s.height_mm,
      rect_px: { ...s.rect_px },
      fit: s.fit,
      allow_pan: s.allow_pan,
      allow_zoom: s.allow_zoom,
      allow_rotate: s.allow_rotate,
    })),
    overlay: template.overlay ? { ...template.overlay } : null,
    dirty: false,
  };
}

/**
 * Updates a slot in the draft with new millimeter properties, automatically recomputing rect_px.
 */
export function updateSlotMm(
  draft: TemplateDraft,
  slotId: string,
  updates: Partial<
    Pick<
      DraftSlot,
      | "x_mm"
      | "y_mm"
      | "width_mm"
      | "height_mm"
      | "fit"
      | "allow_pan"
      | "allow_zoom"
      | "allow_rotate"
    >
  >
): TemplateDraft {
  const dpi = draft.canvas.dpi;
  const nextSlots = draft.slots.map((s) => {
    if (s.id !== slotId) return s;

    const x_mm = updates.x_mm !== undefined ? Math.round(updates.x_mm * 100) / 100 : s.x_mm;
    const y_mm = updates.y_mm !== undefined ? Math.round(updates.y_mm * 100) / 100 : s.y_mm;
    const width_mm =
      updates.width_mm !== undefined ? Math.round(updates.width_mm * 100) / 100 : s.width_mm;
    const height_mm =
      updates.height_mm !== undefined ? Math.round(updates.height_mm * 100) / 100 : s.height_mm;

    const rect_px: PixelRect = {
      left: mmToPx(x_mm, dpi),
      top: mmToPx(y_mm, dpi),
      width: mmToPx(width_mm, dpi),
      height: mmToPx(height_mm, dpi),
    };

    return {
      ...s,
      ...updates,
      x_mm,
      y_mm,
      width_mm,
      height_mm,
      rect_px,
    };
  });

  return {
    ...draft,
    slots: nextSlots,
    dirty: true,
  };
}

/**
 * Updates the canvas parameters and recomputes canvas_px and all slots' rect_px.
 */
export function updateCanvasMm(
  draft: TemplateDraft,
  updates: Partial<DraftCanvas>
): TemplateDraft {
  const nextCanvas: DraftCanvas = {
    ...draft.canvas,
    ...updates,
  };

  const nextCanvasPx = {
    width: mmToPx(nextCanvas.width_mm, nextCanvas.dpi),
    height: mmToPx(nextCanvas.height_mm, nextCanvas.dpi),
  };

  // Recompute slot pixel rectangles if DPI changed
  const nextSlots = draft.slots.map((s) => ({
    ...s,
    rect_px: {
      left: mmToPx(s.x_mm, nextCanvas.dpi),
      top: mmToPx(s.y_mm, nextCanvas.dpi),
      width: mmToPx(s.width_mm, nextCanvas.dpi),
      height: mmToPx(s.height_mm, nextCanvas.dpi),
    },
  }));

  return {
    ...draft,
    canvas: nextCanvas,
    canvas_px: nextCanvasPx,
    slots: nextSlots,
    dirty: true,
  };
}

/**
 * Pure validation for TemplateDraft.
 * Checks DPI bounds, canvas dimensions, slot existence, ID collisions,
 * dimension non-negativity and physical bounding limits.
 */
export function validateTemplateDraft(draft: TemplateDraft): DraftValidationResult {
  const errors: DraftValidationError[] = [];
  const warnings: string[] = [];

  // 1. DPI validation
  if (draft.canvas.dpi <= 0 || !Number.isFinite(draft.canvas.dpi)) {
    errors.push({
      code: "INVALID_DPI",
      message: `DPI deve ser um número positivo maior que zero. Recebido: ${draft.canvas.dpi}`,
    });
  } else if (draft.canvas.dpi < 150) {
    warnings.push(`DPI ${draft.canvas.dpi} é baixo para impressão profissional (recomendado >= 254 DPI).`);
  } else if (draft.canvas.dpi > 600) {
    warnings.push(`DPI ${draft.canvas.dpi} é muito alto e pode causar alto consumo de memória.`);
  }

  // 2. Canvas dimensions validation
  if (draft.canvas.width_mm <= 0 || draft.canvas.height_mm <= 0) {
    errors.push({
      code: "INVALID_CANVAS_DIMENSIONS",
      message: `Dimensões físicas do canvas devem ser maiores que zero (${draft.canvas.width_mm}x${draft.canvas.height_mm} mm).`,
    });
  }

  // 3. Slot presence
  if (!draft.slots || draft.slots.length === 0) {
    errors.push({
      code: "NO_SLOTS",
      message: "O template deve conter pelo menos um slot de foto.",
    });
    return { valid: false, errors, warnings };
  }

  // 4. Slots validation
  const seenIds = new Set<string>();
  const EPSILON_MM = 0.05; // 50 micrometers tolerance for float precision

  for (const slot of draft.slots) {
    if (!slot.id || slot.id.trim() === "") {
      errors.push({
        code: "EMPTY_SLOT_ID",
        message: "Slot possui identificador vazio.",
        slot_id: slot.id,
      });
    } else if (seenIds.has(slot.id)) {
      errors.push({
        code: "DUPLICATE_SLOT_ID",
        message: `ID de slot duplicado: '${slot.id}'.`,
        slot_id: slot.id,
      });
    } else {
      seenIds.add(slot.id);
    }

    if (slot.width_mm <= 0 || slot.height_mm <= 0) {
      errors.push({
        code: "INVALID_SLOT_DIMENSIONS",
        message: `Slot '${slot.id}' possui dimensões inválidas (${slot.width_mm}x${slot.height_mm} mm).`,
        slot_id: slot.id,
      });
    }

    if (slot.x_mm < -EPSILON_MM || slot.y_mm < -EPSILON_MM) {
      errors.push({
        code: "SLOT_OUT_OF_BOUNDS",
        message: `Slot '${slot.id}' posicionado fora da folha à esquerda/topo (X: ${slot.x_mm}mm, Y: ${slot.y_mm}mm).`,
        slot_id: slot.id,
      });
    }

    if (
      slot.x_mm + slot.width_mm > draft.canvas.width_mm + EPSILON_MM ||
      slot.y_mm + slot.height_mm > draft.canvas.height_mm + EPSILON_MM
    ) {
      errors.push({
        code: "SLOT_OUT_OF_BOUNDS",
        message: `Slot '${slot.id}' ultrapassa os limites físicos do canvas (${draft.canvas.width_mm}x${draft.canvas.height_mm} mm).`,
        slot_id: slot.id,
      });
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}
