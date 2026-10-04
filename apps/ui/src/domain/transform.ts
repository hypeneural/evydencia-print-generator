/**
 * Pure slot-transform math defined by ADR-011.
 * TypeScript mirror of apps/desktop/src/evydencia_print_generator/domain/transform.py.
 * Verified against tests/fixtures/transform_vectors.json.
 */

export const SCALE_MIN = 1.0;
export const SCALE_MAX = 8.0;
export const PAN_LIMIT = 1.0;

export interface SlotTransform {
  pan_x_norm: number;
  pan_y_norm: number;
  scale: number;
  rotation_deg: number;
}

export interface Placement {
  effective_scale: number;
  rotation_deg: number;
  center_x: number;
  center_y: number;
  max_dx: number;
  max_dy: number;
}

const EXACT_TRIG: Record<number, [number, number]> = {
  0.0: [1.0, 0.0],
  90.0: [0.0, 1.0],
  "-180": [-1.0, 0.0],
  "-90": [0.0, -1.0],
};

function requireFinite(name: string, val: number): number {
  if (!Number.isFinite(val)) {
    throw new Error(`${name} must be finite`);
  }
  return val;
}

function requirePositive(name: string, val: number): number {
  requireFinite(name, val);
  if (val <= 0) {
    throw new Error(`${name} must be positive`);
  }
  return val;
}

export function normalizeRotation(deg: number): number {
  requireFinite("rotation_deg", deg);
  let norm = ((deg + 180.0) % 360.0);
  if (norm < 0) {
    norm += 360.0;
  }
  norm -= 180.0;
  return Object.is(norm, -0) ? 0 : norm;
}

export function rotationCosSin(rotationDeg: number): [number, number] {
  const deg = normalizeRotation(rotationDeg);
  const exact = EXACT_TRIG[deg];
  if (exact) {
    return exact;
  }
  const rad = (deg * Math.PI) / 180.0;
  return [Math.cos(rad), Math.sin(rad)];
}

export function clamp(val: number, low: number, high: number): number {
  return Math.min(high, Math.max(low, val));
}

export function clampTransform(t: SlotTransform): SlotTransform {
  const panX = requireFinite("pan_x_norm", t.pan_x_norm);
  const panY = requireFinite("pan_y_norm", t.pan_y_norm);
  const scale = requireFinite("scale", t.scale);

  const clampedX = clamp(panX, -PAN_LIMIT, PAN_LIMIT);
  const clampedY = clamp(panY, -PAN_LIMIT, PAN_LIMIT);

  return {
    pan_x_norm: Object.is(clampedX, -0) ? 0 : clampedX,
    pan_y_norm: Object.is(clampedY, -0) ? 0 : clampedY,
    scale: clamp(scale, SCALE_MIN, SCALE_MAX),
    rotation_deg: normalizeRotation(t.rotation_deg),
  };
}

export function rotatedSlotBbox(
  slotW: number,
  slotH: number,
  rotationDeg: number,
): [number, number] {
  requirePositive("slotW", slotW);
  requirePositive("slotH", slotH);
  const [cosT, sinT] = rotationCosSin(rotationDeg);
  const c = Math.abs(cosT);
  const s = Math.abs(sinT);
  return [slotW * c + slotH * s, slotW * s + slotH * c];
}

export function coverScale(
  srcW: number,
  srcH: number,
  slotW: number,
  slotH: number,
  rotationDeg: number,
): number {
  requirePositive("srcW", srcW);
  requirePositive("srcH", srcH);
  const [bboxW, bboxH] = rotatedSlotBbox(slotW, slotH, rotationDeg);
  return Math.max(bboxW / srcW, bboxH / srcH);
}

export function resolvePlacement(
  srcW: number,
  srcH: number,
  slotW: number,
  slotH: number,
  transform: SlotTransform,
): Placement {
  const t = clampTransform(transform);
  const [bboxW, bboxH] = rotatedSlotBbox(slotW, slotH, t.rotation_deg);
  const sEff = t.scale * coverScale(srcW, srcH, slotW, slotH, t.rotation_deg);
  const maxDx = Math.max(0.0, (srcW * sEff - bboxW) / 2.0);
  const maxDy = Math.max(0.0, (srcH * sEff - bboxH) / 2.0);
  const offX = t.pan_x_norm * maxDx;
  const offY = t.pan_y_norm * maxDy;
  const [cosT, sinT] = rotationCosSin(t.rotation_deg);
  const centerX = slotW / 2.0 + cosT * offX - sinT * offY;
  const centerY = slotH / 2.0 + sinT * offX + cosT * offY;

  return {
    effective_scale: sEff,
    rotation_deg: t.rotation_deg,
    center_x: centerX,
    center_y: centerY,
    max_dx: maxDx,
    max_dy: maxDy,
  };
}

export function slotToSourceAffine(
  srcW: number,
  srcH: number,
  p: Placement,
): [number, number, number, number, number, number] {
  const s = p.effective_scale;
  const [cosT, sinT] = rotationCosSin(p.rotation_deg);
  const cx = p.center_x;
  const cy = p.center_y;

  const a = cosT / s;
  const b = sinT / s;
  const c = srcW / 2.0 - (cosT * cx + sinT * cy) / s;
  const d = -sinT / s;
  const e = cosT / s;
  const f = srcH / 2.0 - (-sinT * cx + cosT * cy) / s;

  return [
    Object.is(a, -0) ? 0 : a,
    Object.is(b, -0) ? 0 : b,
    Object.is(c, -0) ? 0 : c,
    Object.is(d, -0) ? 0 : d,
    Object.is(e, -0) ? 0 : e,
    Object.is(f, -0) ? 0 : f,
  ];
}

export function panBySlotDelta(
  srcW: number,
  srcH: number,
  slotW: number,
  slotH: number,
  transform: SlotTransform,
  dxSlot: number,
  dySlot: number,
): SlotTransform {
  requireFinite("dxSlot", dxSlot);
  requireFinite("dySlot", dySlot);
  const t = clampTransform(transform);
  const p = resolvePlacement(srcW, srcH, slotW, slotH, t);
  const [cosT, sinT] = rotationCosSin(t.rotation_deg);

  // Rotate screen delta into photo axes
  const dPhotoX = cosT * dxSlot + sinT * dySlot;
  const dPhotoY = -sinT * dxSlot + cosT * dySlot;

  let panX = t.pan_x_norm;
  let panY = t.pan_y_norm;

  if (p.max_dx > 0) {
    panX += dPhotoX / p.max_dx;
  }
  if (p.max_dy > 0) {
    panY += dPhotoY / p.max_dy;
  }

  return clampTransform({
    pan_x_norm: panX,
    pan_y_norm: panY,
    scale: t.scale,
    rotation_deg: t.rotation_deg,
  });
}
