/**
 * Pure helper for operator slot capabilities.
 * Enforces template allow_pan, allow_zoom, allow_rotate flags.
 */

import type { SlotSpec } from "./types";

export interface OperatorCapabilities {
  canPan: boolean;
  canZoom: boolean;
  canRotate: boolean;
}

export function getOperatorCapabilities(slot?: SlotSpec | null): OperatorCapabilities {
  if (!slot) {
    return { canPan: false, canZoom: false, canRotate: false };
  }
  return {
    canPan: slot.allow_pan !== false,
    canZoom: slot.allow_zoom !== false,
    canRotate: slot.allow_rotate !== false,
  };
}
