import { describe, it, expect } from "vitest";
import transformVectors from "../../../../tests/fixtures/transform_vectors.json";
import {
  clampTransform,
  coverScale,
  resolvePlacement,
  slotToSourceAffine,
  panBySlotDelta,
  type SlotTransform,
} from "./transform";

describe("ADR-011 TypeScript Parity with Python vectors", () => {
  for (const tc of transformVectors.placement_cases) {
    it(`Placement case: ${tc.name}`, () => {
      const [srcW, srcH] = tc.src;
      const [slotW, slotH] = tc.slot;
      const t = tc.transform as SlotTransform;
      const exp = tc.expected;

      const clamped = clampTransform(t);
      expect(clamped.pan_x_norm).toBeCloseTo(exp.clamped.pan_x_norm, 8);
      expect(clamped.pan_y_norm).toBeCloseTo(exp.clamped.pan_y_norm, 8);
      expect(clamped.scale).toBeCloseTo(exp.clamped.scale, 8);
      expect(clamped.rotation_deg).toBeCloseTo(exp.clamped.rotation_deg, 8);

      const cov = coverScale(srcW, srcH, slotW, slotH, clamped.rotation_deg);
      expect(cov).toBeCloseTo(exp.cover_scale, 8);

      const p = resolvePlacement(srcW, srcH, slotW, slotH, t);
      expect(p.effective_scale).toBeCloseTo(exp.effective_scale, 8);
      expect(p.center_x).toBeCloseTo(exp.center[0], 8);
      expect(p.center_y).toBeCloseTo(exp.center[1], 8);
      expect(p.max_dx).toBeCloseTo(exp.max_pan[0], 8);
      expect(p.max_dy).toBeCloseTo(exp.max_pan[1], 8);

      const affine = slotToSourceAffine(srcW, srcH, p);
      for (let i = 0; i < 6; i++) {
        expect(affine[i]).toBeCloseTo(exp.affine[i], 7);
      }
    });
  }

  for (const dc of transformVectors.drag_cases) {
    it(`Drag case: ${dc.name}`, () => {
      const [srcW, srcH] = dc.src;
      const [slotW, slotH] = dc.slot;
      const t = dc.transform as SlotTransform;
      const [dx, dy] = dc.delta;
      const exp = dc.expected;

      const res = panBySlotDelta(srcW, srcH, slotW, slotH, t, dx, dy);
      expect(res.pan_x_norm).toBeCloseTo(exp.pan_x_norm, 8);
      expect(res.pan_y_norm).toBeCloseTo(exp.pan_y_norm, 8);
      expect(res.scale).toBeCloseTo(exp.scale, 8);
    });
  }
});

describe("Photo Cover Invariant: slotToSourceAffine bounds mapping", () => {
  const SLOTS = [
    { name: "Calendario foto_principal", slotW: 823, slotH: 395 },
    { name: "Chaveiro slot 34x44mm", slotW: 402, slotH: 520 },
    { name: "Globo slot 50x80mm", slotW: 591, slotH: 945 },
  ];

  const SOURCES = [
    { name: "Square 1:1", srcW: 3000, srcH: 3000 },
    { name: "Landscape 3:2", srcW: 3000, srcH: 2000 },
    { name: "Portrait 2:3", srcW: 2000, srcH: 3000 },
    { name: "Panoramic 16:9", srcW: 3840, srcH: 2160 },
    { name: "Mobile Story 9:16", srcW: 1080, srcH: 1920 },
  ];

  const TRANSFORMS: Array<{ name: string; transform: SlotTransform }> = [
    { name: "Default (scale=1, pan=0, rot=0)", transform: { scale: 1.0, pan_x_norm: 0, pan_y_norm: 0, rotation_deg: 0 } },
    { name: "Zoomed (scale=2.5, pan=0, rot=0)", transform: { scale: 2.5, pan_x_norm: 0, pan_y_norm: 0, rotation_deg: 0 } },
    { name: "Max pan left (scale=1.5, pan_x=-1)", transform: { scale: 1.5, pan_x_norm: -1.0, pan_y_norm: 0, rotation_deg: 0 } },
    { name: "Max pan right (scale=1.5, pan_x=1)", transform: { scale: 1.5, pan_x_norm: 1.0, pan_y_norm: 0, rotation_deg: 0 } },
    { name: "Max pan top (scale=1.5, pan_y=-1)", transform: { scale: 1.5, pan_x_norm: 0, pan_y_norm: -1.0, rotation_deg: 0 } },
    { name: "Max pan bottom (scale=1.5, pan_y=1)", transform: { scale: 1.5, pan_x_norm: 0, pan_y_norm: 1.0, rotation_deg: 0 } },
    { name: "Rotated 90 deg", transform: { scale: 1.0, pan_x_norm: 0, pan_y_norm: 0, rotation_deg: 90 } },
    { name: "Rotated 180 deg", transform: { scale: 1.0, pan_x_norm: 0, pan_y_norm: 0, rotation_deg: 180 } },
    { name: "Rotated 270 deg", transform: { scale: 1.0, pan_x_norm: 0, pan_y_norm: 0, rotation_deg: -90 } },
  ];

  for (const slot of SLOTS) {
    for (const src of SOURCES) {
      for (const tCase of TRANSFORMS) {
        it(`${slot.name} + ${src.name} under ${tCase.name} covers all 4 corners`, () => {
          const placement = resolvePlacement(src.srcW, src.srcH, slot.slotW, slot.slotH, tCase.transform);
          const [a, b, c, d, e, f] = slotToSourceAffine(src.srcW, src.srcH, placement);

          // 4 corners of the slot: (0,0), (slotW, 0), (0, slotH), (slotW, slotH)
          const corners = [
            { x: 0, y: 0, label: "top-left" },
            { x: slot.slotW, y: 0, label: "top-right" },
            { x: 0, y: slot.slotH, label: "bottom-left" },
            { x: slot.slotW, y: slot.slotH, label: "bottom-right" },
          ];

          const eps = 1e-3;
          for (const pt of corners) {
            // Affine mapping: srcX = a*x + b*y + c, srcY = d*x + e*y + f
            const srcX = a * pt.x + b * pt.y + c;
            const srcY = d * pt.x + e * pt.y + f;

            expect(srcX, `${pt.label} X out of bounds`).toBeGreaterThanOrEqual(-eps);
            expect(srcX, `${pt.label} X exceeds srcW`).toBeLessThanOrEqual(src.srcW + eps);
            expect(srcY, `${pt.label} Y out of bounds`).toBeGreaterThanOrEqual(-eps);
            expect(srcY, `${pt.label} Y exceeds srcH`).toBeLessThanOrEqual(src.srcH + eps);
          }
        });
      }
    }
  }
});
