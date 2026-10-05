import type { PixelRect } from "./types";

/**
 * Pure coordinate mapping from client screen space to Fabric scene space.
 * Follows ADR-011 and Viewport Architecture.
 */
export function pointToScene(
  clientX: number,
  clientY: number,
  canvasRect: { left: number; top: number },
  fitScale: number
): { x: number; y: number } {
  if (fitScale <= 0) {
    throw new Error("fitScale must be positive");
  }
  return {
    x: (clientX - canvasRect.left) / fitScale,
    y: (clientY - canvasRect.top) / fitScale,
  };
}

/**
 * Pure hit-test to check if a scene coordinate (px) falls within a slot's bounding box.
 */
export function findSlotAtScenePoint<T extends { id: string; rect_px: PixelRect }>(
  slots: T[],
  sceneX: number,
  sceneY: number
): T | null {
  for (const slot of slots) {
    const r = slot.rect_px;
    if (
      sceneX >= r.left &&
      sceneX <= r.left + r.width &&
      sceneY >= r.top &&
      sceneY <= r.top + r.height
    ) {
      return slot;
    }
  }
  return null;
}

/**
 * Pure hit-test to check if a screen client coordinate falls within any slot on the canvas.
 */
export function findSlotAtClientPoint<T extends { id: string; rect_px: PixelRect }>(
  slots: T[],
  clientX: number,
  clientY: number,
  canvasBoundingRect: { left: number; top: number; width: number; height: number },
  fitScale: number
): T | null {
  // Check if within canvas bounding box
  if (
    clientX < canvasBoundingRect.left ||
    clientX > canvasBoundingRect.left + canvasBoundingRect.width ||
    clientY < canvasBoundingRect.top ||
    clientY > canvasBoundingRect.top + canvasBoundingRect.height
  ) {
    return null;
  }

  const { x, y } = pointToScene(clientX, clientY, canvasBoundingRect, fitScale);
  return findSlotAtScenePoint(slots, x, y);
}
