/**
 * Pure helpers for rotation user input normalization and parsing.
 * Canonical domain: [-180, 180).
 */

export const ROTATION_MIN = -180.0;
export const ROTATION_MAX_SLIDER = 179.0;
export const ROTATION_MAX_NUMERIC = 179.9;

export function normalizeRotationInput(val: number): number {
  if (!Number.isFinite(val)) return 0.0;
  if (val >= 180.0) {
    return ROTATION_MAX_NUMERIC;
  }
  if (val < -180.0) {
    return ROTATION_MIN;
  }
  return Math.round(val * 10) / 10;
}

export function parseRotationText(text: string, fallbackDeg: number): number {
  const trimmed = text.trim();
  if (!trimmed) return fallbackDeg;
  const num = parseFloat(trimmed);
  if (Number.isNaN(num) || !Number.isFinite(num)) {
    return fallbackDeg;
  }
  return normalizeRotationInput(num);
}
