/**
 * Pure keyboard policy for the Operator editor (testable without a DOM).
 */

/** Products where the Delete key removes the active slot photo. */
export const DELETE_PHOTO_PRODUCTS: ReadonlySet<string> = new Set([
  "chaveiro-3x4",
  "globo-neve",
]);

export interface KeyTargetLike {
  tagName?: string;
  isContentEditable?: boolean;
  closest?: (selector: string) => unknown;
}

const TEXT_TAGS = new Set(["INPUT", "TEXTAREA", "SELECT"]);

/** True when keyboard focus is inside a field where Delete/Ctrl+Z must stay native. */
export function isTextEditingTarget(target: KeyTargetLike | null | undefined): boolean {
  if (!target) return false;
  const tag = (target.tagName || "").toUpperCase();
  if (TEXT_TAGS.has(tag)) return true;
  if (target.isContentEditable) return true;
  if (typeof target.closest === "function") {
    const hit = target.closest('[contenteditable=""], [contenteditable="true"], [role="textbox"]');
    if (hit) return true;
  }
  return false;
}

export interface DeletePhotoKeyContext {
  key: string;
  ctrlKey: boolean;
  altKey: boolean;
  metaKey: boolean;
  shiftKey?: boolean;
  target: KeyTargetLike | null | undefined;
  mode: "operator" | "manager";
  templateId: string | null | undefined;
  activeSlotId: string | null | undefined;
  hasPhotoInActiveSlot: boolean;
}

export function shouldHandleDeletePhoto(ctx: DeletePhotoKeyContext): boolean {
  if (ctx.key !== "Delete") return false;
  if (ctx.ctrlKey || ctx.altKey || ctx.metaKey || ctx.shiftKey) return false;
  if (ctx.mode !== "operator") return false;
  if (!ctx.templateId || !DELETE_PHOTO_PRODUCTS.has(ctx.templateId)) return false;
  if (!ctx.activeSlotId || !ctx.hasPhotoInActiveSlot) return false;
  if (isTextEditingTarget(ctx.target)) return false;
  return true;
}
