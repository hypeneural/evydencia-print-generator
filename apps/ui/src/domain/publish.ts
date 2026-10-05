import type { TemplateDraft } from "./draft";
import type { TemplateModel } from "./types";

export type BumpType = "patch" | "minor" | "major";

/**
 * Computes next semver version string strictly following X.Y.Z format.
 */
export function computeNextVersion(
  currentVersion: string,
  bumpType: BumpType = "minor"
): string {
  const match = currentVersion.trim().match(/^(\d+)\.(\d+)\.(\d+)$/);
  if (!match) {
    return "1.1.0";
  }

  let major = parseInt(match[1], 10);
  let minor = parseInt(match[2], 10);
  let patch = parseInt(match[3], 10);

  if (bumpType === "patch") {
    patch += 1;
  } else if (bumpType === "minor") {
    minor += 1;
    patch = 0;
  } else if (bumpType === "major") {
    major += 1;
    minor = 0;
    patch = 0;
  }

  return `${major}.${minor}.${patch}`;
}

/**
 * Heuristically suggests bump type based on changes made between original template and draft.
 * - Changing canvas size or adding/removing slots suggests "minor".
 * - Minor positional tweaks or permission edits suggest "patch".
 */
export function suggestBumpType(
  original: TemplateModel | null,
  draft: TemplateDraft
): BumpType {
  if (!original) return "minor";

  // Check canvas dimension changes
  if (
    original.canvas.width_mm !== draft.canvas.width_mm ||
    original.canvas.height_mm !== draft.canvas.height_mm ||
    original.canvas.dpi !== draft.canvas.dpi
  ) {
    return "minor";
  }

  // Check slot count
  if (original.slots.length !== draft.slots.length) {
    return "minor";
  }

  // Check slot IDs
  const origIds = new Set(original.slots.map((s) => s.id));
  const draftIds = new Set(draft.slots.map((s) => s.id));
  for (const id of draftIds) {
    if (!origIds.has(id)) return "minor";
  }

  return "patch";
}

/**
 * Strips UI-only derived fields (rect_px, canvas_px, dirty) from draft for bridge payload.
 */
export function cleanDraftForPublish(draft: TemplateDraft): Record<string, unknown> {
  return {
    id: draft.id,
    template_version: draft.template_version,
    name: draft.name,
    status: "production",
    canvas: {
      width_mm: draft.canvas.width_mm,
      height_mm: draft.canvas.height_mm,
      dpi: draft.canvas.dpi,
    },
    slots: draft.slots.map((s) => ({
      id: s.id,
      x_mm: s.x_mm,
      y_mm: s.y_mm,
      width_mm: s.width_mm,
      height_mm: s.height_mm,
      fit: s.fit,
      allow_pan: s.allow_pan,
      allow_zoom: s.allow_zoom,
      allow_rotate: s.allow_rotate,
    })),
    overlay: draft.overlay
      ? {
          path: draft.overlay.path,
          required: Boolean(draft.overlay.required),
        }
      : null,
  };
}
